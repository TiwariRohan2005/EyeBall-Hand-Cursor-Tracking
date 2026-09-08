import ctypes
from ctypes import wintypes
import time

class ContextAnalyzer:
    """
    Background non-blocking service tracking the exact Windows application 
    in the foreground. Eliminates the need for bulky psutil pip packages.
    """
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.psapi = ctypes.windll.psapi
        
        self.last_check = 0
        self.cache_duration = 0.5 # Wait half a second before stressing the OS again
        
        self.current_app = "Unknown"
        self.current_mode = "General Desktop"
        
        # Categorization Dictionary Mapping Raw Executables to Broad Interaction Intent Modes
        self.mode_map = {
            # Web Browsers
            "chrome.exe": "Web Browsing",
            "msedge.exe": "Web Browsing",
            "firefox.exe": "Web Browsing",
            "opera.exe": "Web Browsing",
            
            # Media Players
            "vlc.exe": "Media",
            "spotify.exe": "Media",
            "wmplayer.exe": "Media",
            
            # Presentation / Reading
            "powerpnt.exe": "Presentation",
            "acrobat.exe": "Reading",
            
            # Coding
            "code.exe": "Coding",
            "devenv.exe": "Coding",
            "pycharm64.exe": "Coding"
        }

    def _get_active_process_name(self):
        hwnd = self.user32.GetForegroundWindow()
        if not hwnd: return "workspace.exe"
        
        pid = ctypes.c_ulong()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # 0x0400 | 0x0010 = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        hProcess = self.kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
        if not hProcess: return "workspace.exe"
        
        buffer = ctypes.create_unicode_buffer(512)
        self.psapi.GetModuleBaseNameW(hProcess, None, buffer, 512)
        self.kernel32.CloseHandle(hProcess)
        return buffer.value.lower()

    def update(self):
        """
        Polls the OS periodically. Returns True if the context has significantly shifted.
        """
        now = time.time()
        if now - self.last_check < self.cache_duration:
            return False
            
        self.last_check = now
        new_app = self._get_active_process_name()
        
        if new_app != self.current_app:
            self.current_app = new_app
            self.current_mode = self.mode_map.get(self.current_app, "General Desktop")
            return True
            
        return False
