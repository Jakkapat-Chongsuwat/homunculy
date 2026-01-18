/** LiveKit WebRTC interop for Blazor. */

import {
    Room,
    RoomEvent,
    createLocalAudioTrack,
    type LocalAudioTrack,
    type RemoteTrack
} from "livekit-client";

type DotNetRef = {
    invokeMethodAsync: (method: string, ...args: unknown[]) => Promise<void>;
};

let room: Room | null = null;
let localAudio: LocalAudioTrack | null = null;
let dotNetRef: DotNetRef | null = null;

const audioHostId = "livekit-audio";

const getAudioHost = (): HTMLElement | null =>
    document.getElementById(audioHostId);

const clearAudioHost = () => {
    const host = getAudioHost();
    if (!host) return;
    host.innerHTML = "";
};

const attachTrack = (track: RemoteTrack) => {
    const host = getAudioHost();
    if (!host) return;
    const element = track.attach();
    element.setAttribute("data-livekit-track", track.sid ?? "");
    host.appendChild(element);
};

const decodePayload = (payload: Uint8Array): string =>
    new TextDecoder().decode(payload);

const emitMessage = (message: string, sender: string, timestamp: string) => {
    if (!dotNetRef) return;
    dotNetRef.invokeMethodAsync("OnLiveKitMessage", message, sender, timestamp);
};

const connect = async (url: string, token: string) => {
    if (room) {
        await disconnect();
    }

    room = new Room({
        adaptiveStream: true,
        dynacast: true
    });

    room.on(RoomEvent.TrackSubscribed, (track: RemoteTrack) => {
        if (track.kind === "audio") {
            attachTrack(track);
        }
    });

    room.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
        if (track.kind === "audio") {
            track.detach().forEach((el) => el.remove());
        }
    });

    room.on(RoomEvent.DataReceived, (payload, participant) => {
        const raw = decodePayload(payload);
        const sender = participant?.identity ?? "agent";
        const timestamp = new Date().toISOString();

        try {
            const parsed = JSON.parse(raw) as { message?: string; text?: string };
            const message = parsed.message ?? parsed.text ?? raw;
            emitMessage(message, sender, timestamp);
            return;
        } catch {
            emitMessage(raw, sender, timestamp);
        }
    });

    room.on(RoomEvent.Disconnected, () => {
        clearAudioHost();
    });

    await room.connect(url, token);
};

const setMicEnabled = async (enabled: boolean) => {
    if (!room) return;

    if (!enabled) {
        if (localAudio) {
            await room.localParticipant.unpublishTrack(localAudio);
            localAudio.stop();
            localAudio = null;
        }
        return;
    }

    if (!localAudio) {
        localAudio = await createLocalAudioTrack();
        await room.localParticipant.publishTrack(localAudio);
    }
};

const sendText = async (text: string) => {
    if (!room) return;
    const payload = new TextEncoder().encode(JSON.stringify({ type: "text", message: text }));
    await room.localParticipant.publishData(payload);
};

const disconnect = async () => {
    if (!room) return;

    try {
        if (localAudio) {
            await room.localParticipant.unpublishTrack(localAudio);
            localAudio.stop();
            localAudio = null;
        }
        await room.disconnect();
    } finally {
        room = null;
        clearAudioHost();
    }
};

const isConnected = () => Boolean(room && room.state === "connected");

const registerMessageHandler = (ref: DotNetRef | null) => {
    dotNetRef = ref;
};

const unregisterMessageHandler = () => {
    dotNetRef = null;
};

interface LiveKitInterop {
    connect(url: string, token: string): Promise<void>;
    disconnect(): Promise<void>;
    setMicEnabled(enabled: boolean): Promise<void>;
    isConnected(): boolean;
    sendText(text: string): Promise<void>;
    registerMessageHandler(ref: DotNetRef | null): void;
    unregisterMessageHandler(): void;
}

const livekitInterop: LiveKitInterop = {
    connect,
    disconnect,
    setMicEnabled,
    isConnected,
    sendText,
    registerMessageHandler,
    unregisterMessageHandler
};

declare global {
    interface Window {
        livekitInterop: LiveKitInterop;
    }
}

window.livekitInterop = livekitInterop;

export { livekitInterop };
