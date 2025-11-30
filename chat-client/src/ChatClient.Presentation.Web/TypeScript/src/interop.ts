/** .NET JSInterop bridge for audio player. */

import { WebAudioPlayer } from './audio';

const player = new WebAudioPlayer();

interface AudioPlayerInterop {
    initialize(): Promise<boolean>;
    enqueue(base64Data: string): Promise<void>;
    flush(): void;
    stop(): void;
    reset(): void;
    clear(): void;
    isEnabled(): boolean;
}

const audioPlayerInterop: AudioPlayerInterop = {
    initialize: () => player.initialize(),
    enqueue: (data: string) => player.enqueue(data),
    flush: () => player.flush(),
    stop: () => player.stop(),
    reset: () => player.reset(),
    clear: () => player.clear(),
    isEnabled: () => player.isEnabled
};

declare global {
    interface Window { audioPlayerInterop: AudioPlayerInterop; }
}

window.audioPlayerInterop = audioPlayerInterop;

export { audioPlayerInterop };
