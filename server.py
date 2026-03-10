import asyncio, websockets, json, os, mimetypes
from urllib.parse import urlsplit, unquote
from websockets.datastructures import Headers
from websockets.http11 import Response
from handlers.websocket_utils import send_to_client, heartbeat, broadcast_to_all, broadcast_to_all_except, broadcast_to_channel_except, broadcast_to_voice_channel_with_viewers
from handlers.auth import handle_authentication
from handlers import message as message_handler
from handlers.rate_limiter import RateLimiter
from db import serverEmojis
import watchers
from plugin_manager import PluginManager
from logger import Logger

class OriginChatsServer:
    """OriginChats WebSocket server"""
    
    def __init__(self, config_path="config.json"):
        # Load configuration
        with open(os.path.join(os.path.dirname(__file__), config_path), "r") as f:
            self.config = json.load(f)
        
        # Server state
        self.connected_clients = set()
        self.version = self.config["service"]["version"]
        self.heartbeat_interval = 30
        self.main_event_loop = None
        self.file_observer = None
        self.slash_commands = {}
        
        self.voice_channels = {}
        
        # Initialize rate limiter if enabled
        rate_config = self.config.get("rate_limiting", {})
        if rate_config.get("enabled", False):
            self.rate_limiter = RateLimiter(
                messages_per_minute=rate_config.get("messages_per_minute", 30),
                burst_limit=rate_config.get("burst_limit", 5),
                cooldown_seconds=rate_config.get("cooldown_seconds", 60)
            )
        else:
            self.rate_limiter = None
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager()
        
        Logger.info(f"OriginChats WebSocket Server v{self.version} initialized")
        if self.rate_limiter:
            Logger.info(f"Rate limiting enabled: {rate_config.get('messages_per_minute', 30)} msg/min, burst: {rate_config.get('burst_limit', 5)}")
        else:
            Logger.warning("Rate limiting disabled")

    def _resolve_emoji_file_path(self, file_name):
        """
        Resolve and validate custom emoji file path in db/serverEmojis.
        Returns absolute file path or None when invalid/missing.
        """
        if not file_name:
            return None

        if file_name != os.path.basename(file_name) or file_name.startswith("."):
            return None

        if not serverEmojis.is_allowed_file_type(file_name):
            return None

        emoji_dir = os.path.join(os.path.dirname(__file__), "db", "serverEmojis")
        file_path = os.path.normpath(os.path.join(emoji_dir, file_name))
        emoji_dir_norm = os.path.normpath(emoji_dir)

        if not file_path.startswith(emoji_dir_norm + os.sep):
            return None

        if not os.path.isfile(file_path):
            return None

        return file_path

    def _serve_file_response(self, file_path, cache_control="public, max-age=3600"):
        with open(file_path, "rb") as f:
            body = f.read()

        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"

        return Response(
            200,
            "OK",
            Headers(
                [
                    ("Content-Type", content_type),
                    ("Content-Length", str(len(body))),
                    ("Cache-Control", cache_control),
                ]
            ),
            body,
        )

    async def _process_http_request(self, connection, request):
        """
        Serve HTTP emoji assets on the same socket as WebSocket traffic.
        """
        upgrade = request.headers.get("Upgrade", "")
        connection_hdr = request.headers.get("Connection", "")
        connection_tokens = {token.strip().lower() for token in connection_hdr.split(",") if token.strip()}
        is_websocket_upgrade = upgrade.lower() == "websocket" and "upgrade" in connection_tokens
        if is_websocket_upgrade:
            # Let websockets handle normal WS handshakes.
            return None

        path = urlsplit(request.path).path
        if path in ("/", "/index.html"):
            index_path = os.path.join(os.path.dirname(__file__), "index.html")
            if not os.path.isfile(index_path):
                return Response(
                    404,
                    "Not Found",
                    Headers([("Content-Type", "text/plain; charset=utf-8")]),
                    b"index.html not found",
                )
            return self._serve_file_response(index_path, cache_control="no-cache")

        if not path.startswith("/emojis/"):
            return Response(
                404,
                "Not Found",
                Headers([("Content-Type", "text/plain; charset=utf-8")]),
                b"Not found",
            )

        file_name = unquote(path[len("/emojis/"):]).strip()
        file_path = self._resolve_emoji_file_path(file_name)
        if not file_path:
            return Response(
                404,
                "Not Found",
                Headers([("Content-Type", "text/plain; charset=utf-8")]),
                b"Emoji not found",
            )

        return self._serve_file_response(file_path, cache_control="public, max-age=3600")

    async def handle_client(self, websocket):
        """WebSocket connection handler"""
        # Get client info
        headers = websocket.request.headers
        client_ip = headers.get('CF-Connecting-IP') or headers.get('X-Forwarded-For') or websocket.remote_address[0]
        Logger.add(f"New connection from {client_ip}")
        
        # Add to connected clients
        self.connected_clients.add(websocket)
        Logger.info(f"Total connected clients: {len(self.connected_clients)}")
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat(websocket, self.heartbeat_interval))
        
        try:
            # Send handshake message
            await send_to_client(websocket, {
                "cmd": "handshake",
                "val": {
                    "server": self.config["server"],
                    "limits": self.config["limits"],
                    "version": "1.1.0",
                    "validator_key": "originChats-" + self.config["rotur"]["validate_key"]
                }
            })
                
            # Keep connection open and handle client messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle authentication
                    if data.get("cmd") == "auth" and not getattr(websocket, "authenticated", False):
                        # Create server data object for authentication
                        auth_server_data = {
                            "connected_clients": self.connected_clients,
                            "config": self.config,
                            "plugin_manager": self.plugin_manager,
                            "rate_limiter": self.rate_limiter
                        }
                        await handle_authentication(
                            websocket, data, self.config, 
                            self.connected_clients, client_ip, auth_server_data
                        )
                        continue

                    # Require authentication for other commands
                    if not getattr(websocket, "authenticated", False):
                        await send_to_client(websocket, {"cmd": "auth_error", "val": "Authentication required"})
                        continue

                    # Create server data object for message handler
                    server_data = {
                        "connected_clients": self.connected_clients,
                        "config": self.config,
                        "plugin_manager": self.plugin_manager,
                        "rate_limiter": self.rate_limiter,
                        "send_to_client": send_to_client,
                        "slash_commands": self.slash_commands,
                        "voice_channels": self.voice_channels
                    }

                    listener = data.get("listener")
                    if listener and not isinstance(listener, str):
                        Logger.warning(f"Invalid listener type: {type(listener)}")
                        listener = None
                    # Handle message
                    response = await message_handler.handle(websocket, data, server_data)
                    
                    if not response:
                        Logger.warning(f"No response for message: {data}")
                        continue
                    
                    if response.get("global", False):
                        # Check if this is a channel-specific message
                        if response.get("channel"):
                            # Broadcast only to users who have access to the channel
                            await broadcast_to_channel_except(self.connected_clients, response, response["channel"], websocket)
                        else:
                            # Broadcast to all clients if no channel specified
                            await broadcast_to_all_except(self.connected_clients, response, websocket)
                        
                        if listener:
                            response["listener"] = listener
                        await send_to_client(websocket, response)
                        continue

                    if response:
                        if listener:
                            response["listener"] = listener
                        await send_to_client(websocket, response)

                except json.JSONDecodeError:
                    Logger.error(f"Received invalid JSON: {message[:50]}...")
                except Exception as e:
                    Logger.error(f"Error processing message: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            Logger.info(f"Connection closed by {client_ip}")
        except Exception as e:
            Logger.error(f"Error handling connection: {str(e)}")
        finally:
            heartbeat_task.cancel()
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)
                Logger.delete(f"Client {client_ip} removed. {len(self.connected_clients)} clients remaining")

                username = getattr(websocket, "username", "")

                if getattr(websocket, "authenticated", False):
                    user_id = getattr(websocket, "user_id", None)
                    current_voice_channel = getattr(websocket, "voice_channel", None)

                    if user_id and current_voice_channel:
                        if current_voice_channel in self.voice_channels and user_id in self.voice_channels[current_voice_channel]:
                            msg = {"cmd": "voice_user_left", "channel": current_voice_channel, "username": username}
                            await broadcast_to_voice_channel_with_viewers(
                                self.connected_clients,
                                self.voice_channels,
                                msg,
                                msg,
                                current_voice_channel
                            )

                            del self.voice_channels[current_voice_channel][user_id]

                            if not self.voice_channels[current_voice_channel]:
                                del self.voice_channels[current_voice_channel]

                    ws_id = id(websocket)
                    if ws_id in self.slash_commands:
                        command_names = list(self.slash_commands[ws_id].keys())
                        if command_names:
                            await broadcast_to_all(self.connected_clients, {
                                "cmd": "slash_remove",
                                "commands": command_names
                            })
                            Logger.info(f"Removed {len(command_names)} slash commands for connection {ws_id}")
                        del self.slash_commands[ws_id]

                await broadcast_to_all(self.connected_clients, {
                    "cmd": "user_disconnect",
                    "username": username
                })
    
    async def broadcast_wrapper(self, message):
        """Wrapper for broadcast_to_all to maintain compatibility with watchers"""
        await broadcast_to_all(self.connected_clients, message)
    
    async def start_server(self):
        """Start the WebSocket server"""
        # Store the main event loop for use in other threads
        self.main_event_loop = asyncio.get_event_loop()

        # Setup file watchers for users.json and channels.json
        self.file_observer = watchers.setup_file_watchers(self.broadcast_wrapper, self.main_event_loop)

        # Get port from config or use default
        port = self.config.get("websocket", {}).get("port", 5613)
        host = self.config.get("websocket", {}).get("host", "127.0.0.1")
        
        Logger.info(f"Starting WebSocket server on {host}:{port}")
        
        # Trigger server_start event for plugins
        server_data = {
            "connected_clients": self.connected_clients,
            "config": self.config,
            "plugin_manager": self.plugin_manager,
            "rate_limiter": self.rate_limiter
        }
        self.plugin_manager.trigger_event("server_start", None, {}, server_data)
        
        try:
            async with websockets.serve(
                self.handle_client,
                host,
                port,
                ping_interval=None,
                process_request=self._process_http_request,
            ):
                Logger.success(f"WebSocket server running at ws://{host}:{port}")
                
                # Keep the server running
                await asyncio.Future()
        finally:
            # Stop file watcher when server stops
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()
                Logger.info("File watcher stopped")
