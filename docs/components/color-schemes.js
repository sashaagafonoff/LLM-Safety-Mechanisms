// Dynamic color scheme generation for categories and providers
// Ported from Observable notebook cell: `colorSchemes`

export function generateColorSchemes(categories, providers, d3) {
  const categoryNames = categories.map((c) => c.name).sort();
  const providerNames = providers.map((p) => p.name).sort();

  function generateColors(items, saturation = 0.7, lightness = 0.5) {
    const colorMap = {};
    const hueStep = 360 / items.length;
    items.forEach((item, i) => {
      colorMap[item] = d3.hsl(i * hueStep, saturation, lightness).toString();
    });
    return colorMap;
  }

  return {
    categoryColors: generateColors(categoryNames, 0.6, 0.55),
    providerColors: generateColors(providerNames, 0.5, 0.6)
  };
}
