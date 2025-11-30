import { Observable } from 'rxjs';

export interface IAudioAdapter {
    readonly ready$: Observable<void>;
    readonly ended$: Observable<void>;
    readonly error$: Observable<Error>;
    append(data: ArrayBuffer): Promise<void>;
    end(): void;
    dispose(): void;
}
