// Converts every GIF under the gallery folders into the animated WebP the site
// actually serves, then writes the legacy-URL redirect map.
//
//   public/gifz/<name>.gif                 ->  public/gifz/<name>.webp
//   public/gifz/sub/<name>.gif             ->  public/gifz/sub/<name>.webp
//   public/superdupersecretgifs/<name>.gif ->  public/superdupersecretgifs/<name>.webp
//   (sources removed; same rule for both folders)
//
//   public/_redirects  ->  /gifz/<name>.gif  /gifz/<name>.webp  301
//                          /superdupersecretgifs/<name>.gif  /superdupersecretgifs/<name>.webp  301
//
// The WebP averages ~0.49 MB against ~3.3 MB for the source GIF (17x smaller).
// That matters twice over: public/ is uploaded as-is on every deploy, and the
// gallery downloads the file.
//
// Runs as `prebuild`, so a newly scraped GIF is converted on the next build and
// only converted once: a manifest records the source size each variant came
// from (mtimes do not survive git checkouts). Pass --force to re-encode
// everything and --keep-sources to leave the GIFs in place.
import { readdirSync, readFileSync, writeFileSync, statSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import sharp from 'sharp';

// One entry per gallery. Order matters only in that the /gifz rules stay first
// in public/_redirects.
const TARGETS = [
  { src: 'public/gifz', base: '/gifz', manifest: '.cache/gifz-webp.json' },
  {
    src: 'public/superdupersecretgifs',
    base: '/superdupersecretgifs',
    manifest: '.cache/secretgifs-webp.json',
  },
];
const REDIRECTS = 'public/_redirects';
const MAX_EDGE = 480;
const QUALITY = 70;

const force = process.argv.includes('--force');
const keepSources = process.argv.includes('--keep-sources');
const bytes = (p) => statSync(p).size;

// Recursive: subfolders (a staging area like gifz/tosort) must not ship raw
// GIFs either. Paths are relative to the target folder and always use forward
// slashes.
const walk = (dir) =>
  readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) return walk(full);
    return entry.isFile() ? [relative(dir, full).split(sep).join('/')] : [];
  });

// Kept out of public/ so it is never uploaded. Only a local shortcut: a fresh
// clone already contains the WebP files, so nothing is re-encoded there.
const readManifest = (path) => {
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch {
    return {};
  }
};

async function convertTarget({ src, base, manifest: manifestPath }) {
  mkdirSync(src, { recursive: true });
  mkdirSync(dirname(manifestPath), { recursive: true });

  const manifest = readManifest(manifestPath);
  const gifs = walk(src).filter((f) => f.endsWith('.gif'));
  const toRemove = [];
  let encoded = 0;
  let saved = 0;

  const jobs = gifs.map((name) => async () => {
    const file = join(src, name);
    const out = join(src, `${name.replace(/\.gif$/i, '')}.webp`);
    const size = bytes(file);

    // A file still being written by a scraper can be smaller than what was
    // encoded last time; treat that as stale and redo it next build.
    const fresh = !force && manifest[name]?.bytes === size;
    const missing = !statSync(out, { throwIfNoEntry: false });

    if (!fresh || missing) {
      try {
        await sharp(file, { animated: true })
          .resize({ width: MAX_EDGE, height: MAX_EDGE, fit: 'inside', withoutEnlargement: true })
          .webp({ quality: QUALITY, effort: 4 })
          .toFile(out);
      } catch (error) {
        // Half-downloaded GIFs are skipped rather than failing the deploy.
        console.warn(`skipping ${base}/${name}: ${error.message.split('\n')[0]}`);
        return;
      }
      encoded++;
    }

    manifest[name] = { bytes: size, webp: bytes(out) };
    saved += size - bytes(out);
    if (!keepSources) toRemove.push(file);
  });

  // sharp does the work off-thread; a few in flight keeps every core busy.
  let i = 0;
  await Promise.all(
    Array.from({ length: 4 }, async () => {
      while (i < jobs.length) await jobs[i++]();
    }),
  );

  // Second pass: libvips can still hold a freshly decoded source open on
  // Windows, so removing it inside the encode job fails with EPERM.
  let removed = 0;
  for (const file of toRemove) {
    try {
      rmSync(file, { maxRetries: 10, retryDelay: 100 });
      removed++;
    } catch (error) {
      console.warn(`could not remove ${file}: ${error.code}`);
    }
  }

  const webps = walk(src).filter((f) => f.endsWith('.webp'));

  for (const name of Object.keys(manifest)) {
    if (!gifs.includes(name) && !webps.includes(name.replace(/\.gif$/i, '.webp'))) delete manifest[name];
  }
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');

  const total = webps.reduce((n, f) => n + bytes(join(src, f)), 0);
  console.log(
    `${base}: ${webps.length} webp (${(total / 1048576).toFixed(1)} MB), ` +
      `encoded ${encoded}, removed ${removed} gif, ${(saved / 1048576).toFixed(0)} MB saved`,
  );

  return { base, webps, encoded, removed, saved };
}

const results = [];
for (const target of TARGETS) results.push(await convertTarget(target));

// One static rule per file: placeholders cannot rewrite an extension, and
// Pages allows 2,000 static rules - far above the ~1,075 we have.
const rules = [
  '# Generated by scripts/optimize_gifs.mjs - do not edit by hand.',
  '# Old GIF links (bookmarks, Discord embeds) keep working via the WebP twin.',
  ...results.flatMap(({ base, webps }) =>
    webps.map((f) => `${base}/${f.replace(/\.webp$/i, '.gif')}  ${base}/${f}  301`),
  ),
  '',
].join('\n');
writeFileSync(REDIRECTS, rules);
