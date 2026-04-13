'use client';

import { useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase } from '@/lib/api-base';

export default function PreparationPage() {
  const router = useRouter();
  const apiUrl = useMemo(() => getApiBase(), []);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [resumeText, setResumeText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSelectedFile(e.target.files?.[0] ?? null);
  }

  async function saveCandidateProfile(): Promise<number> {
    if (resumeText.trim()) {
      const res = await fetch(`${apiUrl}/candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText.trim() }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? '経歴書の保存に失敗しました');
      }
      const { id } = await res.json();
      return id;
    }

    if (selectedFile) {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const res = await fetch(`${apiUrl}/candidate/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? '経歴書の読み込みに失敗しました');
      }
      const { id } = await res.json();
      return id;
    }

    throw new Error('経歴書を入力またはファイルで指定してください');
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const candidateId = await saveCandidateProfile();

      const jobRes = await fetch(`${apiUrl}/job`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_description: jobDescription }),
      });
      if (!jobRes.ok) {
        const body = await jobRes.json().catch(() => null);
        throw new Error(body?.detail ?? '案件情報の保存に失敗しました');
      }
      const { id: jobId } = await jobRes.json();

      const prepRes = await fetch(`${apiUrl}/interview-preparation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: candidateId, job_id: jobId }),
      });
      if (!prepRes.ok) {
        const body = await prepRes.json().catch(() => null);
        throw new Error(body?.detail ?? '準備シートの生成に失敗しました');
      }
      const data = await prepRes.json();

      router.push(`/preparation/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成に失敗しました');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">面談前準備</div>
            <h1>準備シートを作成する</h1>
          </div>
        </div>

        <form onSubmit={onSubmit} className="form-grid">

          {/* 経歴書テキスト入力（主導線） */}
          <label>
            経歴書（テキスト入力）
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={8}
              placeholder={
                '候補者の経歴・スキル・実績を貼り付けてください。\n例：Javaを中心に7年間、金融系の業務システム開発に従事。直近ではSpring Bootを使ったAPIサーバー構築を主導し、処理性能を40%改善。日本語N3。'
              }
            />
          </label>

          {/* ファイルアップロード（サブ導線） */}
          <div>
            <div className="meta-label" style={{ marginBottom: 8 }}>
              または経歴書ファイルをアップロード
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                type="button"
                className="button secondary"
                style={{ alignSelf: 'flex-start' }}
                onClick={() => fileInputRef.current?.click()}
              >
                ファイルを選択
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.pdf,.docx"
                onChange={onFileChange}
                style={{ display: 'none' }}
              />
              {selectedFile ? (
                <p style={{ margin: 0, fontSize: 14 }}>
                  選択中：<strong>{selectedFile.name}</strong>
                </p>
              ) : (
                <p className="meta-label" style={{ margin: 0 }}>
                  対応形式：.txt / .pdf / .docx（テキスト入力がある場合はそちらを優先）
                </p>
              )}
            </div>
          </div>

          {/* 案件情報 */}
          <label>
            案件情報
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={6}
              placeholder={
                '案件の概要・必須スキル・業務内容を貼り付けてください。\n例：金融系SaaSのバックエンド開発。Java/Spring Boot必須。チーム5名、スクラム開発。面談45分。'
              }
              required
            />
          </label>

          {error && <p className="error-text">{error}</p>}

          <div className="button-row">
            <button className="button primary" type="submit" disabled={loading}>
              {loading ? '生成中...' : '生成する'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
