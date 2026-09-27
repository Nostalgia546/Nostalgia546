// Original upstream renderer, pinned in the workflow; it receives aggregate data only.
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const upstream = path.resolve(process.argv[2] || '.profile-renderer');
const ts = require(path.join(upstream, 'node_modules/typescript'));
const output = path.join(upstream, 'dist0');
fs.mkdirSync(output, {recursive: true});
for (const name of fs.readdirSync(path.join(upstream, 'src')).filter(name => name.endsWith('.ts'))) {
  let source = fs.readFileSync(path.join(upstream, 'src', name), 'utf8');
  if (name === 'create-pie-language.ts') {
    source = source.replace('userInfo.totalCommitContributions - sumContrib',
      'userInfo.contributesLanguage.reduce((sum, lang) => sum + lang.contributions, 0) - sumContrib');
    source = source.replace("const OTHER_NAME = 'other';", "const OTHER_NAME = '其他';");
  }
  const result = ts.transpileModule(source, {compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019, esModuleInterop: true,
  }});
  fs.writeFileSync(path.join(output, name.replace(/\.ts$/, '.js')), result.outputText);
}
const {createSvg} = require(path.join(output, 'create-svg.js'));
const {NormalSettings} = require(path.join(output, 'color-template.js'));
const data = JSON.parse(fs.readFileSync(path.join(root, 'data/profile.json'), 'utf8'));
const counts = data.days.map(day => day.contributionCount).filter(Boolean).sort((a,b) => a-b);
const threshold = [0.25, 0.5, 0.75].map(q => counts[Math.floor((counts.length-1)*q)] || 0);
const languages = Object.entries(data.languages).filter(([name]) => name !== 'C++').sort((a,b) => b[1]-a[1]);
const top = languages.slice(0, 7).map(([name, size]) => ({language: name,
  color: data.language_colors[name] || '#777777', contributions: size}));
const remainder = languages.slice(7).reduce((sum, item) => sum+item[1], 0);
if (remainder) top.push({language:'其他',color:'#777777',contributions:remainder});
const info = {
  isHalloween:false,
  contributionCalendar:data.days.map(day => ({date:new Date(day.date+'T00:00:00Z'),
    contributionCount:day.contributionCount,
    contributionLevel:day.contributionCount ? 1+threshold.filter(t => day.contributionCount>t).length : 0})),
  contributesLanguage:top, totalContributions:data.total_contributions,
  ...data.contribution_totals, totalForkCount:data.forks,totalStargazerCount:data.stars,
};
const settings = {...NormalSettings,l10n:{commit:'提交',repo:'仓库',review:'审查',pullreq:'拉取请求',issue:'议题',contrib:'次贡献'}};
for (const [name, animated] of [['profile-green.svg',false],['profile-green-animate.svg',true]]) {
  let svg = createSvg(info, settings, animated);
  // The language pie represents filtered code bytes, not per-language commits.
  svg = svg.replace(/<title>([^<]+)<\/title>/g, (match, content) => {
    const value = content.match(/^(.*) (\d+)$/);
    const isLanguage = value && (value[1] === '其他' || languages.some(item => item[0] === value[1]));
    return isLanguage ? `<title>${value[1]}：${(100*Number(value[2])/languages.reduce((s,x)=>s+x[1],0)).toFixed(1)}%</title>` : match;
  });
  fs.writeFileSync(path.join(root, 'profile-3d-contrib', name), svg);
}
console.log('Original green 3D charts generated from anonymous aggregates; C++ excluded.');
