/**
 * Length-prefixed JSON framing for Unix stream sockets (SYS-IPC-001).
 * 4-byte big-endian uint32 length prefix, then UTF-8 JSON body. Max 16 MB.
 */
import * as net from "node:net";

const MAX_MSG = 16 * 1024 * 1024;

export function sendMsg(sock: net.Socket, obj: unknown): void {
  const body = Buffer.from(JSON.stringify(obj));
  if (body.length > MAX_MSG) throw new Error(`message too large: ${body.length}`);
  const hdr = Buffer.alloc(4);
  hdr.writeUInt32BE(body.length, 0);
  sock.write(Buffer.concat([hdr, body]));
}

export function recvMsg(sock: net.Socket): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let needed = 4;
    let headerRead = false;
    let bodyLen = 0;

    const onData = (chunk: Buffer): void => {
      chunks.push(chunk);
      const total = Buffer.concat(chunks);
      if (!headerRead && total.length >= 4) {
        bodyLen = total.readUInt32BE(0);
        if (bodyLen > MAX_MSG) {
          sock.off("data", onData);
          sock.off("error", onError);
          reject(new Error(`message too large: ${bodyLen}`));
          return;
        }
        headerRead = true;
        needed = 4 + bodyLen;
      }
      if (headerRead && total.length >= needed) {
        sock.off("data", onData);
        sock.off("error", onError);
        resolve(JSON.parse(total.slice(4, needed).toString("utf8")));
      }
    };
    const onError = (err: Error): void => {
      sock.off("data", onData);
      reject(err);
    };
    sock.on("data", onData);
    sock.once("error", onError);
  });
}
