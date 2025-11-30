import { IAudioAdapter } from './audio-adapter';
import { HowlerAudioAdapter } from './howler-audio-adapter';
import { isIOS } from './platform';

export const createAudioAdapter = (): IAudioAdapter => {
    const platform = isIOS() ? 'iOS' : 'Desktop';
    console.log('[Audio] Platform:', platform);
    return new HowlerAudioAdapter(platform);
};
