/** Reactive audio player facade for .NET interop. */

import { IAudioPlayer } from './interfaces';
import { AudioStream } from './stream';

export class WebAudioPlayer implements IAudioPlayer {
    private stream = new AudioStream();
    private _isEnabled = false;

    get isEnabled(): boolean { return this._isEnabled; }

    initialize = async (): Promise<boolean> => (this._isEnabled = true, true);
    enqueue = async (base64: string): Promise<void> => this.stream.enqueue(this.decode(base64));
    flush = (): void => this.stream.flush();
    stop = (): void => this.stream.clear();
    reset = (): void => this.stream.clear();
    clear = (): void => this.stream.clear();

    private decode = (base64: string): ArrayBuffer =>
        Uint8Array.from(atob(base64), c => c.charCodeAt(0)).buffer as ArrayBuffer;
}
