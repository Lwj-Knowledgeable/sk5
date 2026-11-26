// src/utils/encrypt.ts
// @ts-ignore - crypto-js 类型定义可能不完整
import CryptoJS from 'crypto-js';

const SECRET = 'your-sign-secret-change-in-production'; // 与后端保持一致，必须与后端 ENCRYPT_SECRET 或 SIGN_SECRET 一致

/**
 * 构建加密的认证载荷
 * 流程：字符串 + 时间戳 -> base64 -> AES-256-CBC 加密 -> base64
 * 匹配后端 decrypt_request 的解密结构（IV + ciphertext）
 * 
 * @param base 要加密的字符串（如 'abdaeeifoajn'）
 * @returns 加密后的 base64 字符串
 */
export function buildEncryptedPayload(base: string): string {
  const timestamp = Date.now().toString();
  const joined = `${base}|${timestamp}`;

  // 第一步：将字符串转换为 base64
  const b64 = CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(joined));

  // 第二步：AES-256-CBC 加密
  // 生成 32 字节密钥（SHA256 哈希）
  const key = CryptoJS.SHA256(SECRET);
  
  // 生成随机 IV（16 字节）
  const iv = CryptoJS.lib.WordArray.random(16);
  
  // AES 加密
  const encrypted = CryptoJS.AES.encrypt(b64, key, {
    iv: iv,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7,
  });

  // 第三步：组合 IV + ciphertext，然后 base64 编码
  // 后端期望的格式：IV（16字节）+ ciphertext，然后 base64 编码
  // CryptoJS 的 encrypted 对象包含 ciphertext 和 iv
  // 我们需要手动组合它们
  
  // 直接使用 WordArray 的 concat 方法组合
  const combined = iv.clone();
  combined.concat(encrypted.ciphertext);
  
  // 转换为 base64 字符串
  const result = CryptoJS.enc.Base64.stringify(combined);

  return result;
}