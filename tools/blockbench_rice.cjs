/* Blockbench本体のJava/Project codecで稲・苗・石臼を書き出す。Playwrightは実行環境から指定する。 */
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const target = path.join(root, 'build/rice3d');
const entries = JSON.parse(fs.readFileSync(path.join(target, 'manifest.json'), 'utf8'));
if (!Array.isArray(entries) || entries.length !== 7 || new Set(entries.map(entry => entry.name)).size !== 7 ||
    entries.some(entry => !/^(seedling|stalk|grain|mill|plant_seedling|plant_growing|plant_mature)$/.test(entry.name) ||
      !entry.image?.startsWith('data:image/png;base64,') || !Array.isArray(entry.model?.elements))) {
 throw new Error('Invalid rice manifest: expected 7 named models with embedded PNG textures');
}

(async () => {
 const browser = await chromium.launch({headless: true, ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {}), args: ['--enable-unsafe-swiftshader']});
 try {
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  await page.goto('https://web.blockbench.net/', {waitUntil: 'domcontentloaded', timeout: 60000});
  await page.waitForFunction(() => typeof Codecs !== 'undefined' && !!Codecs.java_block, null, {timeout: 60000});
  for (const folder of ['blockbench/rice','models3d/rice']) fs.mkdirSync(path.join(root,folder),{recursive:true});
  const evidence = [];
  for (const entry of entries) {
   const result = await page.evaluate(async entry => {
    if (typeof Project !== 'undefined' && Project) {Project.saved = true; await Project.close();}
    Codecs.java_block.load(entry.model, {name: entry.name + '.json', path: entry.name + '.json'});
    Project.name = entry.name;
    Project.java_block_version = '1.21.11';
    Project.texture_width = Project.texture_height = 16;
    const texture = Texture.all[0];
    if (!texture) throw new Error('Texture missing: ' + entry.name);
    texture.name = entry.name + '.png'; texture.folder = 'item/rice'; texture.namespace = 'hnmt';
    texture.fromDataURL(entry.image);
    await new Promise((resolve,reject) => {
     const limit = Date.now() + 10000;
     const check = () => {if (texture.img?.complete && texture.img.naturalWidth === 16) resolve(); else if (Date.now()>limit) reject(new Error('Texture load timeout')); else setTimeout(check,30);};check();
    });
    const groups = {};
    for (const cube of Cube.all) {
     const category = entry.name === 'mill' ? (cube.name.startsWith('Base') ? 'Base' : cube.name.startsWith('Handle') ? 'Handle' : 'Top') : cube.name.startsWith('Plant') ? 'Plant' : 'Sprite';
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
   fs.writeFileSync(path.join(root, 'models3d/rice',entry.name+'.json'),JSON.stringify(result.java,null,2)+'\n');
   fs.writeFileSync(path.join(root, 'blockbench/rice',entry.name+'.bbmodel'),typeof result.project==='string'?result.project:JSON.stringify(result.project,null,2));
   const nativeProject = typeof result.project === 'string' ? JSON.parse(result.project) : result.project;
   const png = nativeProject.textures[0].source;
   if (!png?.startsWith('data:image/png;base64,')) throw new Error('Embedded texture missing');
   fs.writeFileSync(path.join(root,'assets/hnmt/textures/item/rice',entry.name+'.png'),Buffer.from(png.split(',')[1],'base64'));
   evidence.push({name:entry.name,version:result.version,cubes:result.cubes,format:result.format});
   console.log(entry.name,result.cubes,result.java.textures);
   await page.evaluate(() => {Preview.selected.resize(); Preview.selected.controls.target.set(8,6,8);Preview.selected.camera.position.set(28,24,32);Preview.selected.camera.zoom = 0.85;Preview.selected.camera.updateProjectionMatrix();Preview.selected.controls.update();Canvas.updateAll();});
   const preview = await page.evaluate(() => new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Blockbench screenshot timed out')), 15000);
    Preview.selected.screenshot({crop: true, width: 512, height: 512}, result => {clearTimeout(timer);resolve(result);});
   }));
   if (!preview?.startsWith('data:image/png;base64,')) throw new Error('Invalid Blockbench preview: '+entry.name);
   fs.writeFileSync(path.join(target, entry.name+'-preview.png'), Buffer.from(preview.split(',')[1], 'base64'));
   await page.screenshot({path:path.join(target,entry.name+'-blockbench.png')});
   await page.evaluate(async ({project,name,count}) => {
    Project.saved = true; await Project.close();
    Codecs.project.load(typeof project === 'string' ? JSON.parse(project) : project, {path:name+'.bbmodel'});
    if (Cube.all.length !== count || Texture.all.length !== 1 || Format.id !== 'java_block') throw new Error('Native project reopen failed: '+name);
    Project.saved = true;
   }, {project:result.project,name:entry.name,count:result.cubes});
  }
  fs.writeFileSync(path.join(target,'blockbench-validation.json'),JSON.stringify(evidence,null,2)+'\n');
 } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
