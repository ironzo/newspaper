from .check_files import check_file, check_file_tool
from .execute_agent import run_agent, run_agent_tool

tools_schemas_map = {
    "run_agent": run_agent_tool,
    "check_file": check_file_tool,
}

tools_functions_map = {
    "run_agent": run_agent,
    "check_file": check_file,
}
