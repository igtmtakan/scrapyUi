/**
 * タイムゾーン設定とユーティリティ関数
 */

// デフォルトタイムゾーン
export const DEFAULT_TIMEZONE = 'Asia/Tokyo';

// 環境変数からタイムゾーンを取得（デフォルトはAsia/Tokyo）
export const TIMEZONE = process.env.NEXT_PUBLIC_TIMEZONE || DEFAULT_TIMEZONE;

/**
 * 現在時刻をアプリケーションのタイムゾーンで取得
 */
export const nowInTimezone = (): Date => {
  return new Date();
};

/**
 * UTC時刻をローカルタイムゾーンに変換
 */
export const utcToLocal = (utcDate: Date | string): Date => {
  const date = typeof utcDate === 'string' ? new Date(utcDate) : utcDate;
  return new Date(date.toLocaleString('en-US', { timeZone: TIMEZONE }));
};

/**
 * ローカル時刻をUTCに変換
 */
export const localToUtc = (localDate: Date): Date => {
  return new Date(localDate.toISOString());
};

/**
 * 日時をフォーマットして表示
 */
export const formatDateTime = (
  date: Date | string,
  options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: TIMEZONE
  }
): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleString('ja-JP', options);
};

/**
 * 相対時間を表示（例：2分前、1時間前）
 */
export const formatRelativeTime = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - dateObj.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return `${diffSeconds}秒前`;
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分前`;
  } else if (diffHours < 24) {
    return `${diffHours}時間前`;
  } else {
    return `${diffDays}日前`;
  }
};

/**
 * 実行時間を計算（開始時刻から現在時刻まで）
 */
export const calculateDuration = (startTime: Date | string, endTime?: Date | string): string => {
  const start = typeof startTime === 'string' ? new Date(startTime) : startTime;
  const end = endTime ? (typeof endTime === 'string' ? new Date(endTime) : endTime) : new Date();
  
  const diffMs = end.getTime() - start.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  
  if (diffHours > 0) {
    return `${diffHours}時間${diffMinutes % 60}分${diffSeconds % 60}秒`;
  } else if (diffMinutes > 0) {
    return `${diffMinutes}分${diffSeconds % 60}秒`;
  } else {
    return `${diffSeconds}秒`;
  }
};

/**
 * タイムゾーン情報を取得
 */
export const getTimezoneInfo = () => {
  return {
    timezone: TIMEZONE,
    offset: new Date().getTimezoneOffset(),
    name: Intl.DateTimeFormat().resolvedOptions().timeZone
  };
};

/**
 * ISO文字列をローカル時刻に変換
 */
export const isoToLocal = (isoString: string): string => {
  const date = new Date(isoString);
  return formatDateTime(date);
};

/**
 * 日付のみを表示
 */
export const formatDate = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: TIMEZONE
  });
};

/**
 * 時刻のみを表示
 */
export const formatTime = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: TIMEZONE
  });
};
