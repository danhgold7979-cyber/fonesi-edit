'use strict';
const domains={YouTube:['youtube.com','google.com'],Facebook:['facebook.com'],TikTok:['tiktok.com'],Instagram:['instagram.com'],Threads:['threads.com','threads.net','instagram.com'],X:['x.com','twitter.com'],Bilibili:['bilibili.com'],Douyin:['douyin.com'],Xiaohongshu:['xiaohongshu.com'],Kuaishou:['kuaishou.com']};
const status=document.getElementById('status');
async function message(value){
  const reply=await chrome.runtime.sendNativeMessage('com.fonesi.bridge',value);
  if(!reply||!reply.ok)throw new Error(reply?.error||'Không nhận được kết quả native host');
  return reply.result;
}
document.getElementById('pair').onclick=async()=>{
  try{const result=await message({type:'pair',code:document.getElementById('code').value.trim()});
    await chrome.storage.local.set({bridgeToken:result.token});document.getElementById('code').value='';status.textContent='Đã ghép hồ sơ. Chọn đúng nền tảng rồi gửi phiên.';
  }catch(error){status.textContent=error.message;}
};
document.getElementById('send').onclick=async()=>{
  try{const {bridgeToken}=await chrome.storage.local.get('bridgeToken');if(!bridgeToken)throw new Error('Cần ghép hồ sơ trước');
    const platform=document.getElementById('platform').value;const cookies=[];
    for(const domain of domains[platform])cookies.push(...await chrome.cookies.getAll({domain}));
    const result=await message({type:'snapshot',platform,token:bridgeToken,cookies});
    status.textContent='Đã gửi phiên: '+result.status+'. Khả năng bộ tải sử dụng phiên cần kiểm tra trên nguồn thực tế.';
  }catch(error){status.textContent=error.message;}
};
async function refreshAuto(){const {syncPlatforms=[]}=await chrome.storage.local.get('syncPlatforms');document.getElementById('auto').checked=syncPlatforms.includes(document.getElementById('platform').value);}
document.getElementById('platform').onchange=refreshAuto;
document.getElementById('auto').onchange=async()=>{const {syncPlatforms=[]}=await chrome.storage.local.get('syncPlatforms');const platform=document.getElementById('platform').value;const list=syncPlatforms.filter(p=>p!==platform);if(document.getElementById('auto').checked)list.push(platform);await chrome.storage.local.set({syncPlatforms:list});};
refreshAuto();
