/** Audio player contract for .NET interop. */

export interface IAudioPlayer {
    readonly isEnabled: boolean;
    initialize(): Promise<boolean>;
    enqueue(base64Data: string): Promise<void>;
    flush(): void;
    stop(): void;
    reset(): void;
    clear(): void;
}
