/** LiveKit WebRTC interop for Blazor. */

import {
    Room,
    RoomEvent,
    createLocalAudioTrack,
    type LocalAudioTrack,
    type RemoteTrack
} from "livekit-client";

let room: Room | null = null;
let localAudio: LocalAudioTrack | null = null;

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

interface LiveKitInterop {
    connect(url: string, token: string): Promise<void>;
    disconnect(): Promise<void>;
    setMicEnabled(enabled: boolean): Promise<void>;
    isConnected(): boolean;
}

const livekitInterop: LiveKitInterop = {
    connect,
    disconnect,
    setMicEnabled,
    isConnected
};

declare global {
    interface Window {
        livekitInterop: LiveKitInterop;
    }
}

window.livekitInterop = livekitInterop;

export { livekitInterop };
