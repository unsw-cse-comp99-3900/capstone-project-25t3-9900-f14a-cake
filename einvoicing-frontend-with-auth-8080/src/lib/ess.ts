import SparkMD5 from 'spark-md5'
import { request } from './request'
export const RULE_SETS = ['AUNZ_PEPPOL_SB_1_0_10','AUNZ_UBL_1_0_10']
export async function xmlToBase64AndMd5(xml: string){ const base64 = btoa(unescape(encodeURIComponent(xml))); const checksum = SparkMD5.hash(base64); return { base64, checksum } }
export async function essValidateMulti(xml: string, rules: string[]){ const { base64, checksum } = await xmlToBase64AndMd5(xml); const dto = { content: base64, checksum, rules }; const res = await request.post('/api/ess/validate', dto); return res.data }
