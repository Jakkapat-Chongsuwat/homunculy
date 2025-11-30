/** Reactive audio chunk processor. */

import { Subject, from, concatMap, takeUntil, finalize } from 'rxjs';
import { MediaSourceAdapter } from './media-source';

export class AudioStream {
    private chunks$ = new Subject<ArrayBuffer>();
    private stop$ = new Subject<void>();
    private adapter: MediaSourceAdapter | null = null;
    private pending = 0;
    private flushing = false;

    enqueue = (data: ArrayBuffer): void => {
        this.ensureAdapter();
        this.pending++;
        console.log('[AudioStream] enqueue, pending:', this.pending);
        this.chunks$.next(data);
    };

    flush = (): void => {
        console.log('[AudioStream] flush called, pending:', this.pending);
        this.flushing = true;
        if (this.pending === 0) {
            console.log('[AudioStream] no pending, ending now');
            this.adapter?.end();
        }
    };

    clear = (): void => (this.stop$.next(), this.dispose());

    private ensureAdapter(): void {
        if (this.adapter) return;
        this.adapter = new MediaSourceAdapter();
        this.subscribe();
    }

    private subscribe(): void {
        this.adapter!.ready$.subscribe(() =>
            this.chunks$.pipe(
                takeUntil(this.stop$),
                concatMap(chunk => from(this.adapter!.append(chunk)).pipe(
                    finalize(() => {
                        this.pending--;
                        console.log('[AudioStream] chunk done, pending:', this.pending, 'flushing:', this.flushing);
                        if (this.flushing && this.pending === 0) {
                            console.log('[AudioStream] all done, ending stream');
                            this.adapter?.end();
                        }
                    })
                ))
            ).subscribe()
        );
        this.adapter!.ended$.subscribe(() => this.dispose());
    }

    private dispose(): void {
        this.adapter?.dispose();
        this.adapter = null;
        this.pending = 0;
        this.flushing = false;
    }
}
