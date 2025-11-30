/** Reactive audio chunk processor. */

import { Subject, from, concatMap, takeUntil } from 'rxjs';
import { MediaSourceAdapter } from './media-source';

export class AudioStream {
    private chunks$ = new Subject<ArrayBuffer>();
    private stop$ = new Subject<void>();
    private adapter: MediaSourceAdapter | null = null;

    enqueue = (data: ArrayBuffer): void => (this.ensureAdapter(), this.chunks$.next(data));
    flush = (): void => this.adapter?.end();
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
                concatMap(chunk => from(this.adapter!.append(chunk)))
            ).subscribe()
        );
        this.adapter!.ended$.subscribe(() => this.dispose());
    }

    private dispose(): void {
        this.adapter?.dispose();
        this.adapter = null;
    }
}
