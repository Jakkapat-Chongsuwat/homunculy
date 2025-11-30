import { Subject, from, concatMap, takeUntil } from 'rxjs';
import { IAudioAdapter } from './audio-adapter';
import { createAudioAdapter } from './audio-adapter-factory';

export class AudioStream {
    private chunks$ = new Subject<ArrayBuffer>();
    private stop$ = new Subject<void>();
    private adapter: IAudioAdapter | null = null;

    enqueue = (data: ArrayBuffer): void => {
        this.ensureAdapter();
        this.chunks$.next(data);
    };

    flush = (): void => {
        setTimeout(() => this.adapter?.end(), 50);
    };

    clear = (): void => {
        this.stop$.next();
        this.dispose();
    };

    private ensureAdapter(): void {
        if (this.adapter) return;
        this.adapter = createAudioAdapter();
        this.bindAdapter();
    }

    private bindAdapter(): void {
        const a = this.adapter!;
        a.ready$.subscribe(() => this.pipeChunks());
        a.ended$.subscribe(() => this.dispose());
    }

    private pipeChunks(): void {
        this.chunks$.pipe(
            takeUntil(this.stop$),
            concatMap(c => from(this.adapter!.append(c)))
        ).subscribe();
    }

    private dispose(): void {
        this.adapter?.dispose();
        this.adapter = null;
    }
}
