import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://nldekfmoswqecdvydoee.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  console.error('Missing SUPABASE_SERVICE_KEY secret!');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Verified Official & Aggregated RSS Feeds for All India, Rajasthan, SSC, Railway, Bank, DSSSB & Central Schemes
const FEEDS = [
  {
    name: 'PIB India - Central Ministries & Sarkari Schemes',
    url: 'https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
    defaultCategory: 'schemes',
    org: 'Government of India (PIB)',
    jobCat: 'Central Government'
  },
  {
    name: 'All India Govt / SSC / Railway / Bank / LIC / DSSSB Updates',
    url: 'https://www.freejobalert.com/feed/',
    defaultCategory: 'jobs',
    org: 'Central / State Recruitment',
    jobCat: 'All India Govt'
  },
  {
    name: 'Rajasthan Government Jobs (RPSC / RSSB / State)',
    url: 'https://www.freejobalert.com/rajasthan-government-jobs/feed/',
    defaultCategory: 'jobs',
    org: 'Rajasthan Government',
    jobCat: 'Rajasthan'
  }
];

function decodeHtml(str = '') {
  return str
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function detectCategory(title, defaultCategory) {
  const t = title.toLowerCase();
  if (t.includes('admit card') || t.includes('hall ticket') || t.includes('call letter')) return 'admitCards';
  if (t.includes('result') || t.includes('score card') || t.includes('merit list') || t.includes('cut off')) return 'results';
  if (t.includes('yojana') || t.includes('scheme') || t.includes('scholarship') || t.includes('ministry')) return 'schemes';
  return defaultCategory;
}

function detectJobSubCategory(title, fallback) {
  const t = title.toLowerCase();
  if (t.includes('rajasthan') || t.includes('rpsc') || t.includes('rssb') || t.includes('rsmssb')) return 'Rajasthan';
  if (t.includes('ssc')) return 'SSC';
  if (t.includes('upsc')) return 'UPSC';
  if (t.includes('railway') || t.includes('rrb') || t.includes('rrc')) return 'Railway';
  if (t.includes('bank') || t.includes('ibps') || t.includes('sbi') || t.includes('rbi') || t.includes('lic')) return 'Banking';
  if (t.includes('dsssb')) return 'DSSSB';
  return fallback;
}

function parseRssItems(xml) {
  const items = [];
  const itemMatches = xml.match(/<item[\s\S]*?<\/item>/gi) || [];
  for (const rawItem of itemMatches.slice(0, 12)) {
    const titleMatch = rawItem.match(/<title>([\s\S]*?)<\/title>/i);
    const linkMatch = rawItem.match(/<link>([\s\S]*?)<\/link>/i);
    const descMatch = rawItem.match(/<description>([\s\S]*?)<\/description>/i);

    const title = decodeHtml(titleMatch ? titleMatch[1] : '');
    let link = decodeHtml(linkMatch ? linkMatch[1] : '');
    if (link.startsWith('http://')) link = link.replace('http://', 'https://');
    const description = decodeHtml(descMatch ? descMatch[1] : '').slice(0, 600);

    if (title && link.startsWith('https://')) {
      items.push({ title: title.slice(0, 145), link, description });
    }
  }
  return items;
}

async function run() {
  // Fetch existing titles & URLs to avoid duplicates
  const { data: existingRows, error: fetchErr } = await supabase
    .from('portal_content')
    .select('title, official_url')
    .limit(500);

  if (fetchErr) {
    console.error('Error reading portal_content:', fetchErr.message);
    process.exit(1);
  }

  const existingTitles = new Set((existingRows || []).map(r => (r.title || '').toLowerCase().trim()));
  const existingUrls = new Set((existingRows || []).map(r => (r.official_url || '').trim()));

  let insertedCount = 0;

  for (const feed of FEEDS) {
    try {
      console.log(`Fetching: ${feed.name}...`);
      const res = await fetch(feed.url, {
        headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ApnaEmitraBot/1.0)' }
      });
      if (!res.ok) {
        console.warn(`Skipped ${feed.name}: HTTP ${res.status}`);
        continue;
      }
      const xml = await res.text();
      const items = parseRssItems(xml);

      for (const item of items) {
        if (existingTitles.has(item.title.toLowerCase()) || existingUrls.has(item.link)) {
          continue;
        }

        const category = detectCategory(item.title, feed.defaultCategory);
        const job_category = detectJobSubCategory(item.title, feed.jobCat);

        const payload = {
          category,
          status: 'draft', // Always saved as Draft for Admin verification!
          title: item.title,
          description: item.description || 'आधिकारिक नोटिफिकेशन और योग्यता विवरण के लिए नीचे दिए गए लिंक की जांच करें।',
          organization: feed.org,
          job_category,
          qualification: 'Notification देखें',
          location: job_category === 'Rajasthan' ? 'Rajasthan' : 'All India',
          vacancies: 'Notification देखें',
          official_url: item.link,
          updated_at: new Date().toISOString()
        };

        const { error: insertErr } = await supabase.from('portal_content').insert([payload]);
        if (!insertErr) {
          existingTitles.add(item.title.toLowerCase());
          existingUrls.add(item.link);
          insertedCount++;
          console.log(`+ Added Draft [${category}]: ${item.title}`);
        }
      }
    } catch (err) {
      console.warn(`Feed error (${feed.name}):`, err.message);
    }
  }

  console.log(`Done! Total new drafts added for Admin review: ${insertedCount}`);
}

run();
