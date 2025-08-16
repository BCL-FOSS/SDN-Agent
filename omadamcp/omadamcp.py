from fastmcp import FastMCP
from sdn_tools.OmadaAPI import OmadaAPI

mcp = FastMCP(name="OmadaAutomation")

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=7000,
        path="/omada/mcp/",
        log_level="debug",
    )