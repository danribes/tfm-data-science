import { UP_IS_BAD } from "../components/KpiRow";

/** The ironic, colloquial line about what the scenario means for whoever
 *  asked, persona by persona. It closes the «Y en corto» paragraph
 *  (personas/enCorto.ts).
 *
 *  Three rules keep the joke honest:
 *  · It is picked, not generated: one line per persona and outcome (better,
 *    worse, no change for that reader), so the same scenario always gets the
 *    same line and none of it is a model improvising about real people.
 *  · Every line opens on the condition («Si en 2050 las cosas quedan así…»):
 *    the irony is about a scenario, never a forecast.
 *  · It punches at the situation or at the system, not at a vulnerable
 *    reader. The child-poverty profile's lines are aimed at the adults.
 */
type Outcome = "mejor" | "peor" | "igual";

const LINES: Record<string, Record<Outcome, string>> = {
  "01": {
    mejor: "Si en {year} las cosas quedan así, el Tesoro te seguirá pagando sin sobresaltos. En renta fija, que tu inversión sea aburrida es el mejor piropo.",
    peor: "Si en {year} las cosas quedan así, igual cobras más cupón. Disfrútalo con moderación: cuando te pagan más por prestar, es que se fían menos de que te lo devuelvan.",
    igual: "Tanto mover palancas para que tu bono ni se inmute. La renta fija, fiel a su apellido.",
  },
  "02": {
    mejor: "Si en {year} las cosas quedan así, los impagos no te quitarán el sueño. Tranquilo: el consejo se apuntará el mérito igualmente.",
    peor: "Si en {year} las cosas quedan así, toca repasar la cartera de impagos. Mira el lado bueno: las comisiones no entienden de ciclos.",
    igual: "Tu balance, igual que ayer. En banca, que no pase nada ya es una buena noticia.",
  },
  "03": {
    mejor: "Si en {year} las cosas quedan así, la hipoteca se vuelve un poco menos monstruo. No lo celebres aún: el piso que te gusta también lo ha visto la inmobiliaria.",
    peor: "Si en {year} las cosas quedan así, el piso de tus sueños se aleja otro poco. Siempre te quedará el alquiler, que tampoco perdona.",
    igual: "Ni sube ni baja: la hipoteca sigue ahí, esperándote con la paciencia de un banco.",
  },
  "04": {
    mejor: "Si en {year} las cosas quedan así, tu empresa respira. Aprovecha para crecer antes de que alguien toque otra palanca.",
    peor: "Si en {year} las cosas quedan así, toca apretarse el cinturón. Mira el lado bueno: emprender siempre fue deporte de riesgo.",
    igual: "Tu negocio, como estaba. En el mundo de la empresa, eso ya es una pequeña victoria.",
  },
  "05": {
    mejor: "Si en {year} las cosas quedan así, tu nómina aguanta el tipo. Mejor no lo comentes muy alto en la cena familiar.",
    peor: "Si en {year} las cosas quedan así, pintan bastos para la nómina pública. Tranquilo: la plaza sigue siendo fija; lo que se mueve es todo lo demás.",
    igual: "Todo igual en el frente de la nómina: plaza fija y pocas sorpresas.",
  },
  "06": {
    mejor: "Si en {year} las cosas quedan así, tienes titular para la próxima rueda de prensa. Que no se note que lo han hecho las palancas.",
    peor: "Si en {year} las cosas quedan así, toca buscar a quién echarle la culpa. Un consejo: la herencia recibida nunca pasa de moda.",
    igual: "Nada se mueve: el momento perfecto para prometer que todo va a cambiar.",
  },
  "07": {
    mejor: "Si en {year} las cosas quedan así, habrá más dinero público en circulación. Que el modelo no mida las comisiones no quiere decir que nadie las cuente.",
    peor: "Si en {year} las cosas quedan así, se acaban las vacas gordas del presupuesto. Tiempos duros para los amigos de lo ajeno.",
    igual: "El presupuesto, quieto. Mal momento para estrenar sociedad pantalla.",
  },
  "08": {
    mejor: "Si en {year} las cosas quedan así, a los peques les espera un futuro algo mejor. Que no se enteren todavía, que pedirán más paga.",
    peor: "Si en {year} las cosas quedan así, a los que hoy van al cole les toca un futuro más cuesta arriba. Menos mal que aún no leen los presupuestos; los mayores, que sí los leen, deberían sonrojarse.",
    igual: "Nada cambia para los más pequeños: heredarán lo mismo que ya iban a heredar, deuda incluida.",
  },
  "09": {
    mejor: "Si en {year} las cosas quedan así, la pensión aguanta. Ya puedes seguir invitando a los nietos… con moderación.",
    peor: "Si en {year} las cosas quedan así, a la pensión le toca estirarse. Siempre te quedará contárselo a los nietos, que para eso tienes tiempo.",
    igual: "La pensión, como estaba. A tu edad, que no haya sorpresas ya es un regalo.",
  },
  "10": {
    mejor: "Si en {year} las cosas quedan así, igual hasta te independizas antes de que tus padres se jubilen. No te emociones: el casero también ha visto el escenario.",
    peor: "Si en {year} las cosas quedan así, la habitación de tu infancia seguirá siendo tuya una temporada más. Mira el lado bueno: la comida de casa no tiene rival.",
    igual: "Nada cambia: seguirás compartiendo piso, y quizá también el wifi del vecino.",
  },
  "11": {
    mejor: "Si en {year} las cosas quedan así, tu contrato indefinido luce todavía mejor. Ya puedes presumir en la cafetería.",
    peor: "Si en {year} las cosas quedan así, vienen curvas. Pero eres indefinido: podrás preocuparte con toda tranquilidad y durante mucho tiempo.",
    igual: "Tu situación, como siempre. Lo indefinido tiene eso: da igual la palanca que muevas.",
  },
  "12": {
    mejor: "Si en {year} las cosas quedan así, el negocio da un respiro. Aprovéchalo antes de que llegue la próxima cuota.",
    peor: "Si en {year} las cosas quedan así, toca hacer números otra vez. Tranquilo: la cuota de autónomos no falla nunca.",
    igual: "Todo igual: seguirás siendo tu propio jefe, tu propio contable y tu propio servicio técnico.",
  },
};

/** Whether a rise is bad news for *this* reader. UP_IS_BAD reads from the
 *  public-finance side; two personas read two series the other way round: a
 *  dearer house is bad news for the buyer, and a bigger pension bill — here,
 *  pensions that keep up with prices — is good news for the retiree. */
const UP_IS_BAD_FOR: Record<string, Record<string, boolean>> = {
  "03": { precio: true, ipv: true },
  "09": { pens: false },
};

export function upIsBadFor(persona: string, series: string): boolean {
  return UP_IS_BAD_FOR[persona]?.[series] ?? UP_IS_BAD.has(series);
}

/** The outcome for the reader: a change that rounds to zero at the series'
 *  own decimals is no change at all. */
export function outcomeFor(persona: string, series: string, delta: number, dec: number): Outcome {
  if (Math.abs(delta) < 0.5 * 10 ** -dec) return "igual";
  return (delta > 0) === upIsBadFor(persona, series) ? "peor" : "mejor";
}

/** The ironic line, or undefined for a persona without one. */
export function sorna(persona: string | undefined, series: string, delta: number,
  dec: number, year: number): string | undefined {
  const lines = persona ? LINES[persona] : undefined;
  if (!lines) return undefined;
  return lines[outcomeFor(persona!, series, delta, dec)].replace("{year}", String(year));
}
