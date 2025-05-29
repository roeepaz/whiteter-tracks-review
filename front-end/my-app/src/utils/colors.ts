export const randomInt = (min: number, max: number) => 
    Math.floor(Math.random() * (max - min + 1)) + min;
  
  export const hslToRgb = (h: number, s: number, l: number): [number, number, number] => {
    s /= 100;
    l /= 100;
  
    const k = (n: number) => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n: number) =>
      l - a * Math.max(-1, Math.min(Math.min(k(n) - 3, 9 - k(n)), 1));
  
    return [Math.round(f(0) * 255), Math.round(f(8) * 255), Math.round(f(4) * 255)];
  };
  
  export const getColor = (): [number, number, number] => {
    const hue = randomInt(0, 360);
    const saturation = randomInt(60, 90);
    const lightness = randomInt(50, 70);
    return hslToRgb(hue, saturation, lightness);
  };
  