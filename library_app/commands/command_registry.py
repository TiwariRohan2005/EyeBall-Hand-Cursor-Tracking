from typing import Dict, List, Optional
import logging
from .command import Command
from library_app.permissions import PermissionManager

logger = logging.getLogger(__name__)

class CommandRegistry:
    def __init__(self):
        # Maps (Context, Intent) -> Command ID
        self._intent_map: Dict[tuple, str] = {}
        # Maps Command ID -> Command
        self._commands: Dict[str, Command] = {}
        
    def register_command(self, cmd: Command, mapped_intents: List[str] = None):
        self._commands[cmd.id] = cmd
        if mapped_intents:
            for intent in mapped_intents:
                self._intent_map[(cmd.context, intent)] = cmd.id
                
    def get_command_by_id(self, cmd_id: str) -> Optional[Command]:
        return self._commands.get(cmd_id)
        
    def resolve_intent(self, context: str, intent: str) -> Optional[Command]:
        cmd_id = self._intent_map.get((context, intent))
        if cmd_id:
            return self.get_command_by_id(cmd_id)
        return None
        
    def execute_command(self, cmd_id: str, user_role: str, *args, **kwargs) -> dict:
        """
        Executes a command by checking its strict permission blocks first.
        Returns a dict with 'status', 'error' or 'result'.
        """
        cmd = self.get_command_by_id(cmd_id)
        if not cmd:
            return {"status": "error", "error": f"Command {cmd_id} not found."}
            
        try:
            if cmd.required_permission:
                PermissionManager.require_permission(user_role, cmd.required_permission)
            
            result = cmd.handler(*args, **kwargs)
            logger.info(f"Command executed successfully: {cmd.id}")
            return {"status": "success", "result": result, "command_name": cmd.display_name}
        except PermissionError as e:
            logger.warning(f"ACCESS_DENIED: User role {user_role} blocked from {cmd.id}")
            return {"status": "denied", "error": str(e)}
        except Exception as e:
            logger.error(f"Error executing command {cmd.id}: {e}")
            return {"status": "error", "error": str(e)}

    def get_available_commands(self, context: str, user_role: str) -> List[Command]:
        available = []
        for cmd in self._commands.values():
            if cmd.context == context:
                if not cmd.required_permission or PermissionManager.has_permission(user_role, cmd.required_permission):
                    available.append(cmd)
        return available
