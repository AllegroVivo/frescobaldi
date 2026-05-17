# cachedproperty.py -- a property that caches its asynchronously computed value
#
# Copyright (c) 2012 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
An advanced property that computes and caches expensive operations
(such as running an external command and reading its output).

A callback when a value is computed/read is also supported.

You may inherit from CachedProperty to implement the logic to compute
or retrieve the value, or you may use the CachedProperty as a decorator,
where the function is called once to return the result or to assign it
to the property.

If you are using the property as a descriptor e.g.:

import cachedproperty

class MyClass(object):
    version = cachedproperty.cachedproperty()

obj = MyClass()

you can retrieve the value with

    obj.version()

Note that, unlike the Python 'property' built-in, parentheses are needed to get
the value. Without parentheses the property itself is returned, which has some
additional features. obj.version() is equivalent to obj.version.get()

If the returned value is None, the property is considered to be unset (i.e.
not set or computed yet). You can force the value to be computed with:

    obj.version.start()

(and be notified when set with:

    obj.version.computed.connect(myfunction)

), and delete the value with:

    del obj.version

You can also assign a value:

    obj.version = 123

In that case, the value will not be computed anymore.

If you want the value now or later, you can also use

    obj.version.callback(myfunction)

which will call myfunction either now or later with the value.

Properties can also depend on each other:

class MyClass(object):

    @cachedproperty.cachedproperty
    def command(self):
        # ....

    @cachedproperty.cachedproperty(depends=command)
    def version(self):
        cmd = self.command()
        # command has already been computed when this function runs.


When used this way, the function can either return the value for the property
or set if directly. If the function returns None, it is assumed to set the
property by itself now or later. If the function returns a different value, the
default implementation sets the property to the returned value.

This module uses the signals module for the callback logic.

"""
from __future__ import annotations

from typing import (
    Callable, Any, Optional, Tuple, Type, Union, Self, overload,
    TypeVar, Literal, Iterable
)
from weakref import WeakKeyDictionary

from signals import Signal

T = TypeVar("T")
V = TypeVar("V")

class CachedProperty[T, V]:
    """An advanced property that can compute and cache expensive operations.

    This can be used to e.g. run an external command and read its output.

    A callback when a value is computed/read is also supported, either via
    the callback() method or the computed() signal.

    """
    _instance: T
    _property: CachedProperty[T, V]

    # descriptor part
    @classmethod
    def cachedproperty(
        cls,
        func: Optional[Callable[..., Any]] = None,
        depends: Optional[Tuple[CachedProperty, ...]] = None
    ) -> Callable[..., Any]:
        """Decorator to make cached properties."""
        if func is not None:
            return cls(func, depends)
        elif depends is None:
            return cls
        def decorator(func):
            return cls(func, depends)
        return decorator

    def __init__(
        self,
        func: Optional[Callable[[T], Optional[V]]] = None,
        depends: Optional[Iterable[CachedProperty]] = None
    ):
        """Initialize the property/descriptor."""
        self._func: Optional[Callable[..., Any]] = func
        if depends is None:
            self._depends = ()
        elif not isinstance(depends, (tuple, list)):
            self._depends = (depends,)
        else:
            self._depends = depends
        self._state: WeakKeyDictionary[T, CachedProperty.State] = WeakKeyDictionary()

    @overload
    def __get__(
        self,
        instance: None,
        cls: Optional[Type[T]] = None
    ) -> Self: ...

    @overload
    def __get__(
        self,
        instance: T,
        cls: Optional[Type[T]] = None
    ) -> CachedProperty[T, V]: ...

    def __get__(
        self,
        instance: Optional[T],
        cls: Optional[Type[T]] = None
    ) -> Union[CachedProperty[T, V], Self]:
        if instance is None:
            return self._func or self  # type: ignore
        return self.bound(instance)

    def __set__(self, instance: Optional[T], value: Any) -> None:
        self.__get__(instance).set(value)

    def __delete__(self, instance: Optional[T]) -> None:
        self.__get__(instance).unset()

    def bound(self, instance: T) -> CachedProperty:
        """Returns a bound instance."""
        cls = type(self)
        prop = cls.__new__(cls)  # type: ignore
        prop._instance = instance
        prop._property = self
        return prop

    # instance part
    class State:
        signal: Signal = Signal()
        def __init__(self):
            self.value: Optional[V] = None
            self.running: bool = False

    def state(self) -> State:
        """Returns the state for the instance."""
        instance = self.instance()
        d = self._property._state
        try:
            state = d[instance]
        except KeyError:
            state = d[instance] = self.State()
        return state

    def instance(self) -> T:
        """The instance we are a property for."""
        return self._instance

    @property
    def computed(self) -> Signal:
        """The signal that is emitted when the value is set."""
        return self.state().signal

    def set(self, value: Optional[V]) -> None:
        """Sets a value.

        If the value is not None, the computed(value) signal is emitted.

        """
        state = self.state()
        state.value = value
        state.running = False
        if value is not None:
            self.computed.emit(value)
            self.computed.clear()

    def unset(self) -> None:
        """Sets the value to None, the property is considered unset."""
        self.state().value = None

    def get(self) -> Optional[V]:
        """Retrieves the value, which may be None (unset)."""
        return self.state().value

    def __call__(self) -> Optional[V]:
        """Retrieves the value, starting the computation if needed.

        If the function immediately returns a value it is returned;
        otherwise None is returned.

        """
        state = self.state()
        if state.value is None:
            self.start()
        return state.value

    def name(self) -> Optional[str]:
        """Returns the name of the property, if given via the function."""
        if self._property._func:
            return self._property._func.__name__

    def isset(self) -> bool:
        """Returns True if the property is set."""
        return self.state().value is not None

    def iscomputing(self) -> bool:
        """Returns True if the property is being computed."""
        return self.state().running

    def callback(self, func: Callable[[V], None]) -> Optional[Literal[True]]:
        """Calls the specified function back with the value.

        If the value already is known, the callback is performed immediately
        (synchronous) and this method returns True.

        If the value yet has to be computed, the function is connected to the
        computed() signal and start() is called, so the function is called later
        with the value. In that case this method returns None.

        """
        value = self.state().value
        if value is not None:
            func(value)
            return True
        self.computed.connect(func)
        self.start()

    def start(self) -> None:
        """Starts the machinery that computes the value.

        This simply happens by calling run(), which should be reimplemented
        to perform the actual action.

        """
        state = self.state()
        if not state.running and state.value is None:
            state.running = True
            self.checkstart()

    def checkstart(self) -> None:
        """Starts if all dependencies are met."""
        for d in self._property._depends:
            prop = d.__get__(self.instance())
            if prop.get() is None:
                prop.computed.connect(self.checkstart)
                prop.start()
                break
        else:
            self.run()

    def run(self) -> None:
        """Starts the computation.

        The result must be set using self.set(value), which will automatically
        call all registered callbacks once.

        The default implementation starts the function, if given on init.

        """
        if self._property._func:
            result = self._property._func(self.instance())
            if result is not None:
                self.set(result)
        else:
            self.set("(null)")


cachedproperty = CachedProperty.cachedproperty
