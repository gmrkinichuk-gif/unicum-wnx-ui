"""Fail closed unless the client's foreground state is the actual hangar."""


def in_hangar():
    try:
        from helpers import isPlayerAccount
        from gui.Scaleform.lobby_entry import getLobbyStateMachine
        from gui.impl.lobby.hangar.states import DefaultHangarState, LegacyHangarState
        machine = getLobbyStateMachine() if isPlayerAccount() else None
        return machine is not None and isinstance(machine.visibleState, (DefaultHangarState, LegacyHangarState))
    except Exception:
        return False


def unobstructed():
    if not in_hangar():
        return False
    try:
        from helpers import dependency
        from skeletons.gui.impl import IGuiLoader
        from frameworks.wulf import WindowLayer, WindowStatus
        manager = dependency.instance(IGuiLoader).windowsManager
        layers = set(getattr(WindowLayer, key) for key in
                     ('WINDOW', 'FULLSCREEN_WINDOW', 'TOP_WINDOW', 'OVERLAY', 'SYSTEM_MESSAGE')
                     if hasattr(WindowLayer, key))
        if not layers or manager is None:
            return False
        def blocks(window):
            if (getattr(window, 'layer', None) not in layers or
                    window.windowStatus in (WindowStatus.DESTROYING, WindowStatus.DESTROYED) or
                    window.isHidden()):
                return False
            # The MoE hangar indicator in the observed modpack uses the WINDOW
            # layer for its permanent badge. A modal instance still blocks.
            if (type(window).__name__ == '_GFMoEBlWindow' and
                    getattr(window, 'decorator', None) is None and not window.isModal()):
                return False
            return True

        blocked = manager.findWindows(blocks)
        return not blocked
    except Exception:
        return False


def subscribe(session, changed):
    try:
        from helpers import dependency
        from skeletons.gui.impl import IGuiLoader
        manager = dependency.instance(IGuiLoader).windowsManager
        for name in ('onWindowStatusChanged', 'onWindowShowingStatusChanged'):
            event = getattr(manager, name, None)
            if event is not None:
                session.subscribe(event, changed)
    except Exception:
        # The periodic check still fails closed if the client API differs.
        pass
