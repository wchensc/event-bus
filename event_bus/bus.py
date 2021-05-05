""" A simple event bus """

from functools import wraps
from threading import Thread
from collections import defaultdict, Counter
from typing import Iterable, Callable, List, Dict, Any, Set, Union

from event_bus.exceptions import EventDoesntExist


class EventBus:
    """ A simple event bus class. """

    # ------------------------------------------
    #   Dunder Attrs
    # ------------------------------------------

    __slots__ = ('_events', '_async_events')

    # ------------------------------------------
    #   Dunder Methods
    # ------------------------------------------

    def __init__(self) -> None:
        """ Creates new EventBus object. """

        self._events = defaultdict(set)  # type: Dict[Any, Set[Callable]]
        self._async_events = defaultdict(set)  # type: Dict[Any, Set[Callable]]

    def __repr__(self) -> str:
        """ Returns EventBus string representation.

        :return: Instance with how many subscribed events.
        """
        return "<{}: {} subscribed events>".format(
            self.cls_name,
            self.event_count
        )

    def __str__(self) -> str:
        """ Returns EventBus string representation.

        :return: Instance with how many subscribed events.
        """

        return "{}".format(self.cls_name)

    # ------------------------------------------
    # Properties
    # ------------------------------------------

    @property
    def event_count(self) -> int:
        """ Sugar for returning total subscribed events.

        :return: Total amount of subscribed events.
        :rtype: int
        """
        return self._subscribed_event_count()

    @property
    def cls_name(self) -> str:
        """ Convenience method to reduce verbosity.

        :return: Name of class
        :rtype: str
        """
        return self.__class__.__name__

    # ------------------------------------------
    # Public Methods
    # ------------------------------------------

    def on(self, event: str, thread: bool = False) -> Callable:
        """ Decorator for subscribing a function to a specific event.

        :param event: Name of the event to subscribe to.
        :type event: str

        :param thread: whether run the callable in a separate thread
        :type thread: bool

        :return: The outer function.
        :rtype: Callable
        """

        def outer(func):
            self.add_event(func, event, thread)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return outer

    def add_event(self, func: Callable, event: str, thread: bool = False) -> None:
        """ Adds a function to a event.

        :param func: The function to call when event is emitted
        :type func: Callable

        :param event: Name of the event.
        :type event: str

        :param thread: whether run the callable in a separate thread
        :type thread: bool
        """
        if self._events[event].__contains__(func) or self._async_events[event].__contains__(func):
            return
        if thread:
            self._async_events[event].add(func)
        else:
            self._events[event].add(func)

    def emit(self, event: str, *args, **kwargs) -> None:
        """ Emit an event and run the subscribed functions.

        :param event: Name of the event.
        :type event: str
        """
        # Run async handlers first
        handler_threads = [
            Thread(target=f, args=args, kwargs=kwargs) for f in
            self._async_event_funcs(event)
        ]

        for h in handler_threads:
            h.start()

        # Then run sync handlers
        for func in self._event_funcs(event):
            func(*args, **kwargs)

    def emit_only(self, event: str, func_names: Union[str, List[str]], *args,
                  **kwargs) -> None:
        """ Specifically only emits certain subscribed events.

        :param event: Name of the event.
        :type event: str

        :param func_names: Function(s) to emit.
        :type func_names: Union[ str | List[str] ]
        """
        if isinstance(func_names, str):
            func_names = [func_names]

        for func in self._async_event_funcs(event):
            if func.__name__ in func_names:
                Thread(target=func, args=args, kwargs=kwargs).start()

        for func in self._event_funcs(event):
            if func.__name__ in func_names:
                func(*args, **kwargs)

    def emit_after(self, event: str) -> Callable:
        """ Decorator that emits events after the function is completed.

        :param event: Name of the event.
        :type event: str

        :return: Callable

        .. note:
            This plainly just calls functions without passing params into the
            subscribed callables. This is great if you want to do some kind
            of post processing without the callable requiring information
            before doing so.
        """

        def outer(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                returned = func(*args, **kwargs)
                self.emit(event)
                return returned

            return wrapper

        return outer

    def remove_event(self, func_name: str, event: str) -> None:
        """ Removes a subscribed function from a specific event.

        :param func_name: The name of the function to be removed.
        :type func_name: str

        :param event: The name of the event.
        :type event: str

        :raise EventDoesntExist if there func_name doesn't exist in event.
        """
        removed = False
        event_funcs_copy = self._events[event].copy()

        for func in self._event_funcs(event):
            if func.__name__ == func_name:
                event_funcs_copy.remove(func)
                removed = True

        if not removed:
            event_funcs_copy = self._async_events[event].copy()
            for func in self._async_event_funcs(event):
                if func.__name__ == func_name:
                    event_funcs_copy.remove(func)
                    removed = True
            if not removed:
                err_msg = "function doesn't exist inside event {} ".format(event)
                raise EventDoesntExist(err_msg)
            else:
                self._async_events[event] = event_funcs_copy
        else:
            self._events[event] = event_funcs_copy

    # ------------------------------------------
    # Private methods.
    # ------------------------------------------

    def _event_funcs(self, event: str) -> Iterable[Callable]:
        """ Returns an Iterable of the functions subscribed to a event.

        :param event: Name of the event.
        :type event: str

        :return: A iterable to do things with.
        :rtype: Iterable
        """
        for func in self._events[event]:
            yield func

    def _async_event_funcs(self, event: str) -> Iterable[Callable]:
        """ Returns an Iterable of the async functions subscribed to a event.

        :param event: Name of the event.
        :type event: str

        :return: A iterable to do things with.
        :rtype: Iterable
        """
        for func in self._async_events[event]:
            yield func

    def _event_func_names(self, event: str) -> List[str]:
        """ Returns string name of each function subscribed to an event.

        :param event: Name of the event.
        :type event: str

        :return: Names of functions subscribed to a specific event.
        :rtype: list
        """
        res = []
        for func in self._events[event]:
            res.append(func.__name__)
        for func in self._async_events[event]:
            res.append(func.__name__)
        return res

    def _subscribed_event_count(self) -> int:
        """ Returns the total amount of subscribed events.

        :return: Integer amount events.
        :rtype: int
        """
        event_counter = Counter()  # type: Dict[Any, int]

        for key, values in self._events.items():
            event_counter[key] = len(values)

        for key, values in self._async_events.items():
            event_counter[key] += len(values)

        return sum(event_counter.values())
