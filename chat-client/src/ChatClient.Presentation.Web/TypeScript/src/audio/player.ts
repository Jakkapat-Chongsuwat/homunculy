import { IAudioPlayer } from './interfaces';
import { AudioStream } from './stream';

export class WebAudioPlayer implements IAudioPlayer {
    private stream = new AudioStream();
    private enabled = false;

    get isEnabled(): boolean { return this.enabled; }

    initialize = async (): Promise<boolean> => (this.enabled = true);

    enqueue = async (b64: string): Promise<void> =>
        this.stream.enqueue(this.decode(b64));

    flush = (): void => this.stream.flush();
    stop = (): void => this.stream.clear();
    reset = (): void => this.stream.clear();
    clear = (): void => this.stream.clear();

    private decode = (b64: string): ArrayBuffer =>
        Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer;
}
