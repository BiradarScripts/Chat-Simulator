# Advanced TCP Chat Server

This is a feature-rich, multi-threaded TCP chat server built in Python. It uses only the standard `socket` and `threading` libraries to manage concurrent users, chat rooms, and a wide variety of real-time commands.

---

## 🚀 Features

* **Multi-threaded Server:** Handles multiple concurrent client connections.
* **User Login:** Secure login with unique username checks.
* **Advanced Chat Rooms:**
    * Join, leave, and create custom rooms (e.g., `#python`, `#gaming`).
    * Users start in a default `#general` room.
* **Multi-Level Messaging:**
    * **Room (MSG):** Send messages only to users in your current room.
    * **Global (GMSG):** Send a server-wide broadcast to all users in all rooms.
    * **Private (DM):** Send a direct message to any user on the server.
* **User Lists:**
    * **Global (WHO):** See a list of *all* users on the server.
    * **Room (RWHO):** See a list of users *only* in your current room.
* **Dynamic Usernames (NICK):** Change your username at any time.
* **Real-time Notifications:**
    * Users are notified when others join, leave, or disconnect from their room.
    * Users are notified of nickname changes.
* **Server Health & Security:**
    * **Idle Timeout:** Automatically disconnects users after 60 seconds of inactivity.
    * **Heartbeat (PING/PONG):** A keep-alive mechanism to check the connection and reset the idle timer.

---

## 📖 Command Reference

Here is a complete list of all commands available to clients.

| Command | Usage | Description |
| :--- | :--- | :--- |
| **LOGIN** | `LOGIN <username>` | Logs you in. Must be the first command. |
| **MSG** | `MSG <text...>` | Sends a message to everyone in your **current room**. |
| **GMSG** | `GMSG <text...>` | Sends a **global** message to **all** users on the server. |
| **DM** | `DM <user> <text...>` | Sends a **private** message to a specific user. |
| **JOIN** | `JOIN <#room>` | Joins a new room. Creates it if it doesn't exist. |
| **LEAVE** | `LEAVE` | Leaves your current room and returns to `#general`. |
| **WHO** | `WHO` | Lists **all** users on the entire server. |
| **RWHO** | `RWHO` | Lists users **only** in your **current room**. |
| **NICK** | `NICK <new-name>` | Changes your username. |
| **PING** | `PING` | Resets your idle timer and gets a `PONG` reply. |
