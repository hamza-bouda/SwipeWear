export interface StyleArchetype {
  id: string;
  label: string;
  imageUrl: string;
}

/**
 * Onboarding style tiles.
 *
 * These were `picsum.photos/seed/<style>` URLs, where the style word is only a
 * hash seed and has no bearing on the picture: "Streetwear" showed a hand on a
 * rainy window, "Vintage" a lion, "Sportswear" a stand of conifers. The first
 * screen a new user sees asked them to pick a wardrobe style from photographs
 * of wildlife and landscapes.
 *
 * Each image below is a real garment from the catalogue, checked by eye against
 * the style it illustrates rather than trusted from its title — the previous
 * placeholders were plausible-looking URLs that nobody had ever looked at.
 *
 * TODO(KAN-89): these are seller photographs, referenced the same way the feed
 * references them. That is fine for listings; onboarding artwork should be
 * properly licensed imagery before launch, and the URLs die if a listing is
 * removed. StyleTile renders the label over a solid tile when the image fails.
 */
export const styleArchetypes: StyleArchetype[] = [
  {
    id: 'streetwear',
    label: 'Streetwear',
    // Nike SB hooded sweatshirt
    imageUrl: 'https://i.ebayimg.com/images/g/uaUAAOSwHCFmYra3/s-l500.jpg',
  },
  {
    id: 'minimalist',
    label: 'Minimalist',
    // Plain black crew-neck tee, no print
    imageUrl: 'https://i.ebayimg.com/images/g/v~sAAeSwe69p-GHZ/s-l500.jpg',
  },
  {
    id: 'vintage',
    label: 'Vintage',
    // Faded cream Nike crewneck with embroidery
    imageUrl: 'https://i.ebayimg.com/images/g/NkcAAOSwoTBmvjeV/s-l500.jpg',
  },
  {
    id: 'sport',
    label: 'Sportswear',
    // Adidas three-stripe track jacket
    imageUrl: 'https://i.ebayimg.com/images/g/f0EAAeSwfdlo33kv/s-l500.jpg',
  },
  {
    id: 'workwear',
    label: 'Workwear',
    // Carhartt hooded fleece, tan
    imageUrl: 'https://i.ebayimg.com/images/g/sjYAAeSwhYVqFXNi/s-l500.jpg',
  },
  {
    id: 'preppy',
    label: 'Preppy',
    // Lacoste polo
    imageUrl: 'https://i.ebayimg.com/images/g/3YcAAOSwYDZgf-QQ/s-l500.jpg',
  },
  {
    id: 'grunge',
    label: 'Grunge',
    // Blue plaid flannel shirt
    imageUrl: 'https://i.ebayimg.com/images/g/MxcAAOSw-kdX16aL/s-l500.jpg',
  },
  {
    id: 'bohemian',
    label: 'Bohemian',
    // Floral long-sleeve dress
    imageUrl: 'https://i.ebayimg.com/images/g/4HEAAeSwwzRqWQM1/s-l500.jpg',
  },
  {
    id: 'techwear',
    label: 'Techwear',
    // The North Face Osito fleece
    imageUrl: 'https://i.ebayimg.com/images/g/EH8AAeSwTLhqO~tB/s-l500.jpg',
  },
  {
    id: 'casual',
    label: 'Casual',
    // Levi's 501 straight jeans
    imageUrl: 'https://i.ebayimg.com/images/g/FNAAAeSwUappsbYF/s-l500.jpg',
  },
];
