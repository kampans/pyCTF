# pyctfnet.py - online multiplayer plumbing for pyCTF (browser only)
# PeerJS (WebRTC) bridge: lobby codes + message passing. Python only calls simple
# methods and polls for messages; all JS lives in GLUE and is evaluated once.

import json
import sys

IN_BROWSER = sys.platform == "emscripten"
if IN_BROWSER:
    import js

# No 0/O or 1/I/L so codes are easy to read out loud.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LEN = 5

ICE_SERVERS = [
    {"urls": ["stun:stun.l.google.com:19302",
              "stun:stun1.l.google.com:19302",
              "stun:stun.cloudflare.com:3478"]},
    {"urls": ["turn:eu-0.turn.peerjs.com:3478", "turn:us-0.turn.peerjs.com:3478"],
     "username": "peerjs", "credential": "peerjsp"},
]
EXTRA_TURN = [{
    "urls": ["turn:relay1.expressturn.com:3478?transport=udp",
             "turn:relay1.expressturn.com:3478?transport=tcp",
             "turns:relay1.expressturn.com:443?transport=tcp"],
    "username": "000000002108216568", # this is a free expressturn account; if you're stealing it you probably need it more than me...
    "credential": "A1MDT6kfBHj7fYdPxVtMuf+Qhdc=",
}]

GLUE = r"""
(() => {
  if (globalThis.pyctfNet) return;
  const ALPHABET = "__ALPHABET__";
  const CODE_LEN = __CODE_LEN__;
  const PEER_SRC = "https://cdn.jsdelivr.net/npm/peerjs@1.5.5/dist/peerjs.min.js";
  const PREFIX = "pyctf-";
  const ICE = __ICE__;
  const PEER_OPTS = { config: { iceServers: ICE } };

  const net = {
    status: "idle",   // idle | loading | waiting | connecting | connected | closed | error
    error: "",
    code: "",
    inbox: [],
    peer: null,
    conn: null,
    timer: null,
    taken: false,
    ice: "",         // last ICE connection state, for diagnostics
    gen: 0,           // bumped on every start/close so stale callbacks are ignored

    close() {
      this.gen++;
      clearTimeout(this.timer);
      try { if (this.conn) this.conn.close(); } catch (e) {}
      try { if (this.peer) this.peer.destroy(); } catch (e) {}
      this.conn = null; this.peer = null; this.inbox = [];
      this.code = ""; this.error = ""; this.taken = false; this.ice = ""; this.status = "idle";
    },

    fail(msg) {
      clearTimeout(this.timer);
      this.error = msg;
      this.status = "error";
    },

    loadLib() {
      return new Promise((resolve, reject) => {
        if (globalThis.Peer) return resolve();
        const s = document.createElement("script");
        s.src = PEER_SRC;
        s.onload = () => resolve();
        s.onerror = () => reject(new Error("Could not load the networking library."));
        document.head.appendChild(s);
      });
    },

    watchIce(conn, g, isGuest) {
      try {
        const pc = conn.peerConnection;
        if (!pc) return;
        pc.addEventListener("iceconnectionstatechange", () => {
          if (g !== this.gen) return;
          this.ice = pc.iceConnectionState;
          if (this.ice === "failed" && this.status !== "connected") {
            if (isGuest) this.fail("Could not set up a direct connection (ICE failed). A strict network may be blocking it.");
            else this.taken = false;   // let the friend try again
          }
        });
      } catch (e) {}
    },

    attach(conn, g, isGuest) {
      this.watchIce(conn, g, isGuest);
      conn.on("open", () => {
        if (g !== this.gen) return;
        this.conn = conn;
        clearTimeout(this.timer);
        this.status = "connected";
      });
      conn.on("data", (d) => { if (g === this.gen) this.inbox.push(d); });
      const lost = () => { if (g === this.gen && this.status === "connected") this.status = "closed"; };
      conn.on("close", lost);
      conn.on("error", lost);
    },

    host() {
      this.close();
      const g = this.gen;
      this.status = "loading";
      this.loadLib().then(() => {
        if (g !== this.gen) return;
        const tryOpen = (attempt) => {
          let code = "";
          for (let i = 0; i < CODE_LEN; i++) code += ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
          const peer = new Peer(PREFIX + code, PEER_OPTS);
          this.peer = peer;
          peer.on("open", () => {
            if (g !== this.gen) return;
            this.code = code;
            this.status = "waiting";
          });
          peer.on("connection", (conn) => {
            if (g !== this.gen) return;
            if (this.taken) { conn.on("open", () => conn.close()); return; }  // lobby is 2 players only
            this.taken = true;
            this.attach(conn, g, false);
          });
          peer.on("error", (e) => {
            if (g !== this.gen || this.status === "connected") return;
            if (e.type === "unavailable-id" && attempt < 5) { peer.destroy(); tryOpen(attempt + 1); return; }
            this.fail("Network error: " + e.type);
          });
        };
        tryOpen(0);
      }).catch((e) => { if (g === this.gen) this.fail(e.message); });
    },

    join(code) {
      this.close();
      const g = this.gen;
      this.status = "loading";
      this.timer = setTimeout(() => {
        if (g === this.gen && this.status !== "connected")
          this.fail("Timed out (ICE: " + (this.ice || "none") + "). Check the code, or your network may block direct connections.");
      }, 20000);
      this.loadLib().then(() => {
        if (g !== this.gen) return;
        const peer = new Peer(undefined, PEER_OPTS);
        this.peer = peer;
        this.status = "connecting";
        peer.on("open", () => {
          if (g !== this.gen) return;
          this.attach(peer.connect(PREFIX + code, { reliable: true }), g, true);
        });
        peer.on("error", (e) => {
          if (g !== this.gen || this.status === "connected") return;
          this.fail(e.type === "peer-unavailable" ? "No lobby found with that code." : "Network error: " + e.type);
        });
      }).catch((e) => { if (g === this.gen) this.fail(e.message); });
    },

    send(s) { if (this.conn && this.conn.open) this.conn.send(s); },

    poll() {
      if (!this.inbox.length) return "";
      const out = this.inbox.join("\n");
      this.inbox = [];
      return out;
    },
  };
  globalThis.pyctfNet = net;
})();
"""


class Net:
    def __init__(self):
        self.available = IN_BROWSER
        self._api = None

    def _get(self):
        if self._api is None:
            js.eval(GLUE.replace("__ALPHABET__", ALPHABET)
                    .replace("__CODE_LEN__", str(CODE_LEN))
                    .replace("__ICE__", json.dumps(ICE_SERVERS + EXTRA_TURN)))
            self._api = js.pyctfNet
        return self._api

    @property
    def status(self):
        return str(self._api.status) if self._api is not None else "idle"

    @property
    def code(self):
        return str(self._api.code) if self._api is not None else ""

    @property
    def error(self):
        return str(self._api.error) if self._api is not None else ""

    def host(self):
        self._get().host()

    def join(self, code):
        self._get().join(code)

    def close(self):
        if self._api is not None:
            self._api.close()

    def send(self, obj):
        if self._api is not None:
            self._api.send(json.dumps(obj, separators=(",", ":")))

    def poll(self):
        """Return every message received since the last call, oldest first."""
        if self._api is None:
            return []
        raw = str(self._api.poll())
        if not raw:
            return []
        out = []
        for line in raw.split("\n"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
        return out