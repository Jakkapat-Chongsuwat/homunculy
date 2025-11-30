export interface IAudioPlayer {
    readonly isEnabled: boolean;
    initialize(): Promise<boolean>;
    enqueue(base64: string): Promise<void>;
    flush(): void;
    stop(): void;
    reset(): void;
    clear(): void;
}
