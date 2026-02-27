import sys
import os
import time
import inspect
import contextvars
import traceback
from typing import Any, Dict, List, Optional, Callable
from importlib.abc import MetaPathFinder, Loader

# Context-safe storage for the current execution chain and stats
_current_chain: contextvars.ContextVar[List[Dict[str, Any]]] = contextvars.ContextVar("engain_chain", default=[])
_current_stats: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar("engain_stats", default={})

def get_chain() -> List[Dict[str, Any]]:
    """Retrieve the instrumentation chain for the current context."""
    return _current_chain.get()

def get_stats() -> Dict[str, Any]:
    """Retrieve the instrumentation stats for the current context."""
    return _current_stats.get()

class EngAInHookFinder(MetaPathFinder):
    """
    Wraps existing meta_path finders to detect when a project module is loaded
    and trigger its __hook__ function if present.
    """
    def __init__(self, roots: List[str]):
        self.roots = [os.path.abspath(r) for r in roots]
        self._loading = False

    def find_spec(self, fullname, path, target=None):
        if self._loading:
            return None
        
        # Avoid recursion when we are doing our own imports
        self._loading = True
        try:
            # We don't find specs ourselves, we just observe the results of others
            # But the requirement is to wrap the loader.
            # In modern Python, we iterate sys.meta_path.
            for finder in sys.meta_path:
                if finder is self:
                    continue
                spec = finder.find_spec(fullname, path, target)
                if spec and spec.loader:
                    # Check if this module is in our project roots
                    origin = spec.origin
                    if origin and any(origin.startswith(root) for root in self.roots):
                        spec.loader = EngAInHookLoader(spec.loader, self.roots)
                    return spec
            return None
        finally:
            self._loading = False

class EngAInHookLoader(Loader):
    """Wraps a loader to trigger __hook__ after execution."""
    def __init__(self, real_loader, roots):
        self.real_loader = real_loader
        self.roots = roots

    def create_module(self, spec):
        return self.real_loader.create_module(spec)

    def exec_module(self, module):
        self.real_loader.exec_module(module)
        # Execution is done, check for hook
        _trigger_module_hook(module, event="import")

def _trigger_module_hook(module, event: str, func_name: Optional[str] = None):
    """Safely calls the __hook__ function if it exists in the module."""
    hook = getattr(module, "__hook__", None)
    if hook and callable(hook):
        chain = get_chain()
        # Guard against recursive hook calls if the hook itself triggers an event
        # (e.g. by calling a function in a hooked module)
        if getattr(hook, "_engain_hook_active", False):
            return
        
        hook._engain_hook_active = True
        try:
            file_path = getattr(module, "__file__", "unknown")
            hook(chain, event=event, module=module.__name__, file=file_path, func=func_name)
        except Exception as e:
            chain.append({
                "type": "hook_error",
                "event": event,
                "module": module.__name__,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
        finally:
            hook._engain_hook_active = False

def _engain_profile_func(frame, event, arg):
    """
    Profile function for sys.setprofile. 
    Tracks 'call' and 'return' events for modules with __hook__.
    """
    if event not in ('call', 'return'):
        return
    
    code = frame.f_code
    module_name = frame.f_globals.get('__name__')
    if not module_name:
        return
    
    module = sys.modules.get(module_name)
    if not module:
        return
    
    # Check if module has a hook
    if not hasattr(module, "__hook__"):
        return
    
    _trigger_module_hook(module, event=event, func_name=code.co_name)

class HookRuntime:
    """
    Manages the lifecycle of an instrumentation chain.
    """
    def __init__(self, roots: List[str], enable_profiling: bool = False, max_events: int = 500):
        self.roots = [os.path.abspath(r) for r in roots]
        self.enable_profiling = enable_profiling
        self.max_events = max_events
        self.finder = EngAInHookFinder(self.roots)

    def run(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Runs a function within a fresh instrumentation context.
        Returns (result, chain).
        """
        chain: List[Dict[str, Any]] = []
        stats: Dict[str, Any] = {}
        
        token_chain = _current_chain.set(chain)
        token_stats = _current_stats.set(stats)
        
        # Install import hooks
        sys.meta_path.insert(0, self.finder)
        
        old_profile = None
        if self.enable_profiling:
            old_profile = sys.getprofile()
            sys.setprofile(_engain_profile_func)

        try:
            # Check existing modules for hooks if they are in root?
            # User said: "checks for a module-level function __hook__ and calls it once" (Import-time)
            # For a long-lived server, we might want to trigger 'init' for already loaded modules
            # that match our filter.
            self._trigger_preloaded_hooks()
            
            result = fn(*args, **kwargs)
            
            # Cap the chain if it grew too large
            if len(chain) > self.max_events:
                summary = {
                    "type": "chain_truncated",
                    "original_size": len(chain),
                    "max_allowed": self.max_events
                }
                final_chain = chain[:self.max_events]
                final_chain.append(summary)
                _current_chain.set(final_chain)
                chain = final_chain

            return result, chain
        finally:
            # Uninstall hooks
            if self.finder in sys.meta_path:
                sys.meta_path.remove(self.finder)
            
            if self.enable_profiling:
                sys.setprofile(old_profile)
                
            _current_chain.reset(token_chain)
            _current_stats.reset(token_stats)

    def _trigger_preloaded_hooks(self):
        """Triggers hooks for modules already in sys.modules that match project roots."""
        for name, module in list(sys.modules.items()):
            if not module: continue
            origin = getattr(module, "__file__", None)
            if origin and any(origin.startswith(root) for root in self.roots):
                if hasattr(module, "__hook__"):
                    _trigger_module_hook(module, event="init")

# Helper to automatically find the project root (EngAIn)
def find_project_root() -> str:
    current = os.path.abspath(__file__)
    while current != os.path.dirname(current):
        if os.path.isdir(os.path.join(current, "EngAIn")):
            return os.path.join(current, "EngAIn")
        # Check if we are already inside EngAIn
        if os.path.basename(current) == "EngAIn":
            return current
        current = os.path.dirname(current)
    # Default to current dir's parent if not found (assuming we are in EngAIn/godotsim/)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
