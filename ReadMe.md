# 田本さんの課題

## 課題の概要

- ユーザーに対していくつか質問をする
- 質問の回答から、ユーザーのニーズ指標(仮)を算出する
- 全ての質問に対する回答受付が終わったタイミングで、ニーズ指標の計算を行い、おススメのスポットを出力する

## 課題の分割

### 機能の洗い出し

#### 質問フェーズ

- 以下のことを繰り返し行う
  - ユーザーに質問する
  - ユーザーの回答を受け付ける
  - ユーザーの回答から、ニーズ指標の計算をする
  - ニーズ指標を算出し、保存する

#### おススメ場所提案フェーズ

- 今まで保存してきたニーズ指標を読み出す
- ニーズ指標に基づいて、何かしらの方法で、おススメスポットを決める
- おススメスポットを提案する

## 課題の進め方について

- いきなりLINE でやろうとすると、バグが起こったときに追跡がしにくくなる
- そのため、まずは上記の課題を手元で実装する。実装がうまくできたら、LINE で動くように移植する

### タスク分割

#### 課題1 ユーザーから受け付けた質問をそのまま表示する

## スケジュール案

- 4回くらいで完成させられるんじゃないかなーと思っています。
  - 手元での実装 1
  - 手元での実装 2
  - 手元での実装 3
  - LINE への移植
