import type { SpeechService } from '../SpeechService'
export class WebSpeechService implements SpeechService { speak(text: string) { speechSynthesis.speak(new SpeechSynthesisUtterance(text)) } stop() { speechSynthesis.cancel() } }
