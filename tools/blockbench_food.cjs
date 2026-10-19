/* Blockbench本体のJava/Project codecで料理を書き出す。Playwrightは実行環境から指定する。 */
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../..');
const target = path.join(root, 'resourcepack-build/food3d');
const entries = JSON.parse(fs.readFileSync(path.join(target, 'manifest.json'), 'utf8'));
if (!Array.isArray(entries) || entries.length !== 32 || new Set(entries.map(entry => entry.name)).size !== 32 ||
    entries.some(entry => !/^(sashimi|nigiri|don|grill|simmer|soup)_[a-z]+$/.test(entry.name) ||
      !entry.image?.startsWith('data:image/png;base64,') || !Array.isArray(entry.model?.elements))) {
 throw new Error('Invalid dish manifest: expected 32 named models with embedded PNG textures');
}

(async () => {
 const browser = await chromium.launch({headless: true, ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {}), args: ['--enable-unsafe-swiftshader']});
 try {
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  await page.goto('https://web.blockbench.net/', {waitUntil: 'domcontentloaded', timeout: 60000});
  await page.waitForFunction(() => typeof Codecs !== 'undefined' && !!Codecs.java_block, null, {timeout: 60000});
  fs.mkdirSync(path.join(root, 'resourcepack/blockbench/dish'), {recursive:true});
  const evidence = [];
  for (const entry of entries) {
   const result = await page.evaluate(async entry => {
    if (typeof Project !== 'undefined' && Project) {Project.saved = true; await Project.close();}
    Codecs.java_block.load(entry.model, {name: entry.name + '.json', path: entry.name + '.json'});
    Project.name = entry.name;
    Project.texture_width = Project.texture_height = 32;
    const texture = Texture.all[0];
    if (!texture) throw new Error('Texture missing: ' + entry.name);
    texture.name = entry.name + '.png'; texture.folder = 'item/dish3d'; texture.namespace = 'hnmt';
    texture.fromDataURL(entry.image);
    await new Promise((resolve,reject) => {
     const limit = Date.now() + 10000;
     const check = () => {if (texture.img?.complete && texture.img.naturalWidth === 32) resolve(); else if (Date.now()>limit) reject(new Error('Texture load timeout')); else setTimeout(check,30);};check();
    });
    const groups = {};
    for (const cube of Cube.all) {
     const category = cube.name.startsWith('vessel_') ? 'Vessel' : cube.name.startsWith('garnish_') ? 'Garnish' : 'Food';
     groups[category] ||= new Group({name:category}).init();
     cube.addTo(groups[category]);
    }
    Canvas.updateAll();
    const java = JSON.parse(Codecs.java_block.compile());
    const project = Codecs.project.compile();
    Project.saved = true;
    return {java,project,version:Blockbench.version,cubes:Cube.all.length,format:Format.id};
   }, entry);
   if (result.format !== 'java_block' || result.java.elements.length !== entry.model.elements.length) throw new Error('Blockbench dropped cubes: '+entry.name);
   fs.writeFileSync(path.join(root,'resourcepack/models3d/dish',entry.name+'.json'),JSON.stringify(result.java,null,2)+'\n');
   fs.writeFileSync(path.join(root,'resourcepack/blockbench/dish',entry.name+'.bbmodel'),typeof result.project==='string'?result.project:JSON.stringify(result.project,null,2));
   evidence.push({name:entry.name,version:result.version,cubes:result.cubes,format:result.format});
   console.log(entry.name,result.cubes,result.java.textures);
   await page.evaluate(() => {Preview.selected.resize(); Preview.selected.controls.target.set(8,3.5,8);Preview.selected.camera.position.set(20,17,24);Preview.selected.controls.update();Canvas.updateAll();});
   const preview = await page.evaluate(() => new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Blockbench screenshot timed out')), 15000);
    Preview.selected.screenshot({crop: true, width: 512, height: 512}, result => {clearTimeout(timer);resolve(result);});
   }));
   if (!preview?.startsWith('data:image/png;base64,')) throw new Error('Invalid Blockbench preview: '+entry.name);
   fs.writeFileSync(path.join(target, entry.name+'-preview.png'), Buffer.from(preview.split(',')[1], 'base64'));
   if (['don_ikura','nigiri_salmon','sashimi_maguro','grill_unagi','soup_tai'].includes(entry.name)) {
    await page.screenshot({path:path.join(target,entry.name+'-blockbench.png')});
   }
  }
  fs.writeFileSync(path.join(target,'blockbench-validation.json'),JSON.stringify(evidence,null,2)+'\n');
 } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
