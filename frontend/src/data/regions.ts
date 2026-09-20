// 国家代码 → 区域列表
// 大国（中/美/德/法/西/英/日/韩）列出全部一级行政区；
// 小国（新加坡）区域等于国家本身。

export const REGIONS_BY_COUNTRY: Record<string, string[]> = {
  // ---------- China：34 个省级行政区 ----------
  CN: [
    'Beijing', 'Tianjin', 'Hebei', 'Shanxi', 'Inner Mongolia',
    'Liaoning', 'Jilin', 'Heilongjiang', 'Shanghai', 'Jiangsu',
    'Zhejiang', 'Anhui', 'Fujian', 'Jiangxi', 'Shandong', 'Henan',
    'Hubei', 'Hunan', 'Guangdong', 'Guangxi', 'Hainan', 'Chongqing',
    'Sichuan', 'Guizhou', 'Yunnan', 'Tibet', 'Shaanxi', 'Gansu',
    'Qinghai', 'Ningxia', 'Xinjiang', 'Hong Kong', 'Macau', 'Taiwan',
  ],

  // ---------- United States：50 州 ----------
  US: [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
    'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
    'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
    'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts',
    'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
    'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico',
    'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma',
    'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
    'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
  ],

  // ---------- Germany：16 个联邦州 ----------
  DE: [
    'Baden-Württemberg', 'Bavaria', 'Berlin', 'Brandenburg', 'Bremen',
    'Hamburg', 'Hesse', 'Lower Saxony', 'Mecklenburg-Vorpommern',
    'North Rhine-Westphalia', 'Rhineland-Palatinate', 'Saarland',
    'Saxony', 'Saxony-Anhalt', 'Schleswig-Holstein', 'Thuringia',
  ],

  // ---------- France：18 个大区（含 5 个海外大区） ----------
  FR: [
    'Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté', 'Brittany',
    'Centre-Val de Loire', 'Corsica', 'Grand Est', 'Hauts-de-France',
    'Île-de-France', 'Normandy', 'Nouvelle-Aquitaine', 'Occitanie',
    'Pays de la Loire', 'Provence-Alpes-Côte d’Azur',
    'Guadeloupe', 'French Guiana', 'Martinique', 'Mayotte', 'Réunion',
  ],

  // ---------- Spain：17 自治区 + 2 自治市 ----------
  ES: [
    'Andalusia', 'Aragon', 'Asturias', 'Balearic Islands',
    'Basque Country', 'Canary Islands', 'Cantabria',
    'Castile and León', 'Castilla-La Mancha', 'Catalonia',
    'Extremadura', 'Galicia', 'La Rioja', 'Community of Madrid',
    'Region of Murcia', 'Navarre', 'Valencian Community',
    'Ceuta', 'Melilla',
  ],

  // ---------- United Kingdom：4 个构成国 ----------
  GB: [
    'England', 'Scotland', 'Wales', 'Northern Ireland',
  ],

  // ---------- Japan：47 个都道府县 ----------
  JP: [
    'Hokkaido', 'Aomori', 'Iwate', 'Miyagi', 'Akita', 'Yamagata',
    'Fukushima', 'Ibaraki', 'Tochigi', 'Gunma', 'Saitama', 'Chiba',
    'Tokyo', 'Kanagawa', 'Niigata', 'Toyama', 'Ishikawa', 'Fukui',
    'Yamanashi', 'Nagano', 'Gifu', 'Shizuoka', 'Aichi', 'Mie',
    'Shiga', 'Kyoto', 'Osaka', 'Hyogo', 'Nara', 'Wakayama',
    'Tottori', 'Shimane', 'Okayama', 'Hiroshima', 'Yamaguchi',
    'Tokushima', 'Kagawa', 'Ehime', 'Kochi', 'Fukuoka', 'Saga',
    'Nagasaki', 'Kumamoto', 'Oita', 'Miyazaki', 'Kagoshima', 'Okinawa',
  ],

  // ---------- South Korea：17 个广域自治团体 ----------
  KR: [
    'Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju', 'Daejeon',
    'Ulsan', 'Sejong', 'Gyeonggi', 'Gangwon',
    'North Chungcheong', 'South Chungcheong',
    'North Jeolla', 'South Jeolla',
    'North Gyeongsang', 'South Gyeongsang', 'Jeju',
  ],

  // ---------- Singapore：小国，区域 = 国家 ----------
  SG: ['Singapore'],
};

/** 根据国家代码获取区域列表；无数据返回空数组 */
export function getRegionsByCountry(countryCode: string): string[] {
  if (!countryCode) return [];
  return REGIONS_BY_COUNTRY[countryCode.toUpperCase()] ?? [];
}