class StyleArchetype {
  const StyleArchetype(this.id, this.label, this.imageUrl);

  final String id;
  final String label;
  final String imageUrl;
}

const styleArchetypes = [
  StyleArchetype(
    'streetwear',
    'Streetwear',
    'https://i.ebayimg.com/images/g/uaUAAOSwHCFmYra3/s-l500.jpg',
  ),
  StyleArchetype(
    'minimalist',
    'Minimaliste',
    'https://i.ebayimg.com/images/g/v~sAAeSwe69p-GHZ/s-l500.jpg',
  ),
  StyleArchetype(
    'y2k',
    'Y2K',
    'https://i.ebayimg.com/images/g/MxcAAOSw-kdX16aL/s-l500.jpg',
  ),
  StyleArchetype(
    'workwear',
    'Workwear',
    'https://i.ebayimg.com/images/g/sjYAAeSwhYVqFXNi/s-l500.jpg',
  ),
  StyleArchetype(
    'grunge',
    'Grunge',
    'https://i.ebayimg.com/images/g/NkcAAOSwoTBmvjeV/s-l500.jpg',
  ),
  StyleArchetype(
    'bohemian',
    'Bohème',
    'https://i.ebayimg.com/images/g/4HEAAeSwwzRqWQM1/s-l500.jpg',
  ),
  StyleArchetype(
    'sport',
    'Sport',
    'https://i.ebayimg.com/images/g/f0EAAeSwfdlo33kv/s-l500.jpg',
  ),
  StyleArchetype(
    'classic',
    'Classique',
    'https://i.ebayimg.com/images/g/3YcAAOSwYDZgf-QQ/s-l500.jpg',
  ),
];

const topSizes = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL'];
const bottomSizes = [
  '28',
  '30',
  '32',
  '34',
  '36',
  '38',
  '40',
  '42',
  '44',
  '46',
];
const shoeSizes = [
  '35',
  '36',
  '37',
  '38',
  '39',
  '40',
  '41',
  '42',
  '43',
  '44',
  '45',
  '46',
];

const availableSizes = [...topSizes, ...bottomSizes, ...shoeSizes];
