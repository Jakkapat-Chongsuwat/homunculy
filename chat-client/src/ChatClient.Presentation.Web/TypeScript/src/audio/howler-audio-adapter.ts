import { Subject } from 'rxjs';
import { Howl, Howler } from 'howler';
import { IAudioAdapter } from './audio-adapter';
import { createWavBlob } from './pcm-utils';

const SILENT_WAV = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';
const UNLOCK_EVENTS = ['click', 'touchstart', 'touchend', 'keydown', 'pointerdown'];

const setupAutoUnlock = (): void => {
    if ((window as any).__howlerUnlock) return;
    (window as any).__howlerUnlock = true;

    const unlock = () => {
        Howler.autoUnlock = true;
        Howler.usingWebAudio = true;
        
        const silent = new Howl({ src: [SILENT_WAV], volume: 0, onend: () => silent.unload() });
        silent.play();
        
        console.log('[Audio] Unlocked');
        UNLOCK_EVENTS.forEach(e => document.removeEventListener(e, unlock, { capture: true }));
    };

    UNLOCK_EVENTS.forEach(e => document.addEventListener(e, unlock, { capture: true, passive: true }));
};

setupAutoUnlock();

export class HowlerAudioAdapter implements IAudioAdapter {
    private chunks: ArrayBuffer[] = [];
    private howl: Howl | null = null;
    private blobUrl: string | null = null;

    readonly ready$ = new Subject<void>();
    readonly ended$ = new Subject<void>();
    readonly error$ = new Subject<Error>();

    constructor(private platform: string) {
        console.log(`[${platform}] Howler adapter`);
        setTimeout(() => this.ready$.next(), 0);
    }

    async append(data: ArrayBuffer): Promise<void> {
        this.chunks.push(data);
    }

    end(): void {
        if (this.chunks.length === 0) return;
        this.play();
    }

    private play(): void {
        const blob = createWavBlob(this.chunks);
        this.blobUrl = URL.createObjectURL(blob);
        console.log(`[${this.platform}] WAV:`, blob.size);

        this.howl = new Howl({
            src: [this.blobUrl],
            format: ['wav'],
            html5: false,
            onplay: () => console.log(`[${this.platform}] Playing`),
            onend: () => this.handleEnd(),
            onloaderror: (_, e) => this.handleError('Load', e),
            onplayerror: (_, e) => this.handleError('Play', e),
        });

        this.howl.play();
    }

    private handleEnd(): void {
        this.cleanup();
        this.ended$.next();
    }

    private handleError(type: string, err: unknown): void {
        console.error(`[${this.platform}] ${type}:`, err);
        this.cleanup();
        this.error$.next(new Error(`${type}: ${err}`));
    }

    private cleanup(): void {
        this.howl?.unload();
        this.howl = null;
        if (this.blobUrl) URL.revokeObjectURL(this.blobUrl);
        this.blobUrl = null;
        this.chunks = [];
    }

    dispose(): void {
        this.howl?.stop();
        this.cleanup();
        this.ready$.complete();
        this.ended$.complete();
        this.error$.complete();
    }
}
