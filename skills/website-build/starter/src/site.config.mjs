// Single source of truth for the business facts used across the site.
// Every value here must come from the owner or their existing materials.
// Leave a field as '' (or []) rather than inventing it; components skip empty fields.
export const site = {
  name: '__NAME__',
  url: 'https://__SLUG__.example.workers.dev',
  // false until launch day: every page carries noindex and robots.txt blocks
  // crawlers, so the workers.dev address stays out of search results while the
  // site is being built. website-launch-care sets this to true at launch.
  launched: false,
  tagline: '',
  description: '',
  // 'en-GB', 'en-US', 'de', 'fr'... match the owner's language and spelling.
  locale: 'en',
  // Shown as written; phoneHref is the same number in international format.
  phone: '',
  phoneHref: '', // e.g. '+441632960960' (no spaces, country code first)
  email: '',
  address: {
    street: '',
    locality: '',
    region: '',
    postalCode: '',
    country: '',
  },
  // Opening hours for people (footer, contact page), e.g. ['Tue to Sat: 9:00 to 17:30', 'Sun and Mon: closed'].
  hoursText: [],
  // The same hours for search engines, schema.org format, e.g. ['Tu-Sa 09:00-17:30'].
  hours: [],
  social: {},
  // schema.org type for the structured data block, e.g. 'LocalBusiness',
  // 'Restaurant', 'Bakery', 'Plumber', 'Dentist', 'ProfessionalService', 'Organization'.
  schemaType: 'LocalBusiness',
  // Cloudflare Web Analytics (cookie-free). website-launch-care sets this to true
  // when the owner switches analytics on at launch; the privacy page follows it.
  analytics: false,
  themeColor: '#111111',
};
