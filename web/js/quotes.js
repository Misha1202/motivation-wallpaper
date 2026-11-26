// Источник цитат: quotes.json (собирается tools/fetch_quotes.py),
// с колодой без повторов и запасным набором на случай офлайна.

const FALLBACK = [
  { text: "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного", ref: "Иоанна 3:16" },
  { text: "Уповай на Господа всем сердцем твоим", ref: "Притчи 3:5" },
  { text: "Господь — Пастырь мой; я ни в чём не буду нуждаться", ref: "Псалом 22:1" },
  { text: "Всё могу в укрепляющем меня Иисусе Христе", ref: "Филиппийцам 4:13" },
  { text: "Свет во тьме светит, и тьма не объяла его", ref: "Иоанна 1:5" },
  { text: "Придите ко Мне все труждающиеся и обременённые, и Я успокою вас", ref: "Матфея 11:28" },
  { text: "Любовь долготерпит, милосердствует, любовь не завидует", ref: "1 Коринфянам 13:4" },
  { text: "Надежда не постыжает", ref: "Римлянам 5:5" },
  { text: "Будьте тверды, непоколебимы, всегда преуспевайте в деле Господнем", ref: "1 Коринфянам 15:58" },
  { text: "Господь — сила моя и песнь моя", ref: "Исход 15:2" },
  { text: "Просите, и дано будет вам; ищите, и найдёте", ref: "Матфея 7:7" },
  { text: "Вера же есть осуществление ожидаемого и уверенность в невидимом", ref: "Евреям 11:1" },
];

const MIN_LENGTH = 12;
const MAX_LENGTH = 360;

function shuffle(items) {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

export class Quotes {
  constructor() {
    this.items = FALLBACK;
    this.pool = FALLBACK;
    this.deck = [];
    this.index = 0;
    this.last = null;
  }

  async load() {
    try {
      const response = await fetch("quotes.json", { cache: "no-cache" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const quotes = Array.isArray(data.quotes) ? data.quotes : [];
      const valid = quotes.filter(
        (quote) =>
          quote &&
          typeof quote.text === "string" &&
          quote.text.length >= MIN_LENGTH &&
          quote.text.length <= MAX_LENGTH,
      );
      if (valid.length >= 20) this.items = valid;
    } catch (error) {
      console.info("quotes.json недоступен, использую запасной набор", error);
    }
    this.pool = this.items;
    this.reshuffle();
    return this.pool.length;
  }

  reshuffle() {
    this.deck = shuffle(this.pool);
    this.index = 0;
    // Не показываем одну и ту же цитату на стыке колод.
    if (this.last && this.deck.length > 1 && this.deck[0] === this.last) {
      const swapIndex = 1 + Math.floor(Math.random() * (this.deck.length - 1));
      [this.deck[0], this.deck[swapIndex]] = [this.deck[swapIndex], this.deck[0]];
    }
  }

  next() {
    if (!this.deck.length) this.reshuffle();
    if (this.index >= this.deck.length) this.reshuffle();
    const quote = this.deck[this.index];
    this.index += 1;
    this.last = quote;
    return quote;
  }
}
