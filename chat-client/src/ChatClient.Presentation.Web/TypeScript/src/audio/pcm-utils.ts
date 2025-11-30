const RATE = 24000;
const CHANNELS = 1;
const BITS = 16;

const writeStr = (v: DataView, o: number, s: string): void =>
    [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));

const totalBytes = (chunks: ArrayBuffer[]): number =>
    chunks.reduce((sum, c) => sum + c.byteLength, 0);

const createHeader = (len: number): ArrayBuffer => {
    const h = new ArrayBuffer(44);
    const v = new DataView(h);
    const align = CHANNELS * (BITS / 8);
    
    writeStr(v, 0, 'RIFF');
    v.setUint32(4, 36 + len, true);
    writeStr(v, 8, 'WAVE');
    writeStr(v, 12, 'fmt ');
    v.setUint32(16, 16, true);
    v.setUint16(20, 1, true);
    v.setUint16(22, CHANNELS, true);
    v.setUint32(24, RATE, true);
    v.setUint32(28, RATE * align, true);
    v.setUint16(32, align, true);
    v.setUint16(34, BITS, true);
    writeStr(v, 36, 'data');
    v.setUint32(40, len, true);
    
    return h;
};

export const createWavBlob = (chunks: ArrayBuffer[]): Blob => {
    const header = createHeader(totalBytes(chunks));
    return new Blob([header, ...chunks], { type: 'audio/wav' });
};
