export interface Country {
  code: string   // ISO 3166-1 alpha-2
  name: string
  dial: string   // international dial code, e.g. "+86"
}

export const COUNTRIES: Country[] = [
  { code: 'AF', name: 'Afghanistan', dial: '+93' },
  { code: 'AR', name: 'Argentina', dial: '+54' },
  { code: 'AU', name: 'Australia', dial: '+61' },
  { code: 'AT', name: 'Austria', dial: '+43' },
  { code: 'BD', name: 'Bangladesh', dial: '+880' },
  { code: 'BE', name: 'Belgium', dial: '+32' },
  { code: 'BR', name: 'Brazil', dial: '+55' },
  { code: 'CA', name: 'Canada', dial: '+1' },
  { code: 'CL', name: 'Chile', dial: '+56' },
  { code: 'CN', name: 'China', dial: '+86' },
  { code: 'CO', name: 'Colombia', dial: '+57' },
  { code: 'CZ', name: 'Czech Republic', dial: '+420' },
  { code: 'DK', name: 'Denmark', dial: '+45' },
  { code: 'EG', name: 'Egypt', dial: '+20' },
  { code: 'FI', name: 'Finland', dial: '+358' },
  { code: 'FR', name: 'France', dial: '+33' },
  { code: 'DE', name: 'Germany', dial: '+49' },
  { code: 'GR', name: 'Greece', dial: '+30' },
  { code: 'HK', name: 'Hong Kong', dial: '+852' },
  { code: 'HU', name: 'Hungary', dial: '+36' },
  { code: 'IN', name: 'India', dial: '+91' },
  { code: 'ID', name: 'Indonesia', dial: '+62' },
  { code: 'IR', name: 'Iran', dial: '+98' },
  { code: 'IE', name: 'Ireland', dial: '+353' },
  { code: 'IL', name: 'Israel', dial: '+972' },
  { code: 'IT', name: 'Italy', dial: '+39' },
  { code: 'JP', name: 'Japan', dial: '+81' },
  { code: 'KZ', name: 'Kazakhstan', dial: '+7' },
  { code: 'KE', name: 'Kenya', dial: '+254' },
  { code: 'KR', name: 'South Korea', dial: '+82' },
  { code: 'KW', name: 'Kuwait', dial: '+965' },
  { code: 'MY', name: 'Malaysia', dial: '+60' },
  { code: 'MX', name: 'Mexico', dial: '+52' },
  { code: 'MA', name: 'Morocco', dial: '+212' },
  { code: 'NL', name: 'Netherlands', dial: '+31' },
  { code: 'NZ', name: 'New Zealand', dial: '+64' },
  { code: 'NG', name: 'Nigeria', dial: '+234' },
  { code: 'NO', name: 'Norway', dial: '+47' },
  { code: 'PK', name: 'Pakistan', dial: '+92' },
  { code: 'PH', name: 'Philippines', dial: '+63' },
  { code: 'PL', name: 'Poland', dial: '+48' },
  { code: 'PT', name: 'Portugal', dial: '+351' },
  { code: 'QA', name: 'Qatar', dial: '+974' },
  { code: 'RO', name: 'Romania', dial: '+40' },
  { code: 'RU', name: 'Russia', dial: '+7' },
  { code: 'SA', name: 'Saudi Arabia', dial: '+966' },
  { code: 'SG', name: 'Singapore', dial: '+65' },
  { code: 'ZA', name: 'South Africa', dial: '+27' },
  { code: 'ES', name: 'Spain', dial: '+34' },
  { code: 'SE', name: 'Sweden', dial: '+46' },
  { code: 'CH', name: 'Switzerland', dial: '+41' },
  { code: 'TW', name: 'Taiwan', dial: '+886' },
  { code: 'TH', name: 'Thailand', dial: '+66' },
  { code: 'TR', name: 'Turkey', dial: '+90' },
  { code: 'UA', name: 'Ukraine', dial: '+380' },
  { code: 'AE', name: 'United Arab Emirates', dial: '+971' },
  { code: 'GB', name: 'United Kingdom', dial: '+44' },
  { code: 'US', name: 'United States', dial: '+1' },
  { code: 'VN', name: 'Vietnam', dial: '+84' },
]

export function findCountryByCode(code: string): Country | undefined {
  return COUNTRIES.find((c) => c.code === code)
}

export function findCountryByDial(dial: string): Country | undefined {
  return COUNTRIES.find((c) => c.dial === dial)
}