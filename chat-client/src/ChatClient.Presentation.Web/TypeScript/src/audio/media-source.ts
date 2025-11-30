/** Reactive MediaSource adapter for streaming audio. */

import { Subject, fromEvent, firstValueFrom } from 'rxjs';
import { take } from 'rxjs/operators';

export class MediaSourceAdapter {
    private mediaSource = new MediaSource();
    private sourceBuffer: SourceBuffer | null = null;
    private audio = document.createElement('audio');
    
    readonly ready$ = new Subject<void>();
    readonly ended$ = new Subject<void>();
    readonly error$ = new Subject<Error>();

    constructor() {
        this.audio.src = URL.createObjectURL(this.mediaSource);
        this.bind();
    }

    private bind(): void {
        fromEvent(this.mediaSource, 'sourceopen').pipe(take(1)).subscribe(() => this.open());
        fromEvent(this.audio, 'canplay').pipe(take(1)).subscribe(() => this.play());
        fromEvent(this.audio, 'ended').subscribe(() => this.ended$.next());
    }

    private open(): void {
        try {
            this.sourceBuffer = this.mediaSource.addSourceBuffer('audio/mpeg');
            this.ready$.next();
        } catch (e) {
            this.error$.next(e as Error);
        }
    }

    private play(): void {
        this.audio.play().catch(e => this.error$.next(e));
    }

    async append(data: ArrayBuffer): Promise<void> {
        if (!this.sourceBuffer) return;
        await this.waitReady();
        this.sourceBuffer.appendBuffer(data);
        await this.waitReady();
    }

    private async waitReady(): Promise<void> {
        if (!this.sourceBuffer?.updating) return;
        await firstValueFrom(fromEvent(this.sourceBuffer, 'updateend').pipe(take(1)));
    }

    end(): void {
        if (this.mediaSource.readyState === 'open') this.mediaSource.endOfStream();
    }

    dispose(): void {
        this.audio.pause();
        this.audio.src = '';
        this.ready$.complete();
        this.ended$.complete();
        this.error$.complete();
    }
}
