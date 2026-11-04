"""Streamlit Community Cloud: repository entrypoint = app.py.
Python 3.10+. 실행: streamlit run app.py
5→9 변환은 공식 환산이 아닌 백분위 중앙값 기반 보간 추정입니다.
"""
import math
from html import escape
import streamlit as st

SEMESTERS = ['1학년 1학기', '1학년 2학기', '2학년 1학기', '2학년 2학기', '3학년 1학기']
FIVE = [1., 2., 3., 4., 5.]
P5 = [5., 22., 50., 78., 95.]
P9 = [2., 7.5, 17., 31.5, 50., 68.5, 83., 92.5, 98.]
NINE = [float(i) for i in range(1, 10)]
SOURCE = 'https://ipsi.jinhak.or.kr/ssenjh/data/notice_view.do?idx=592'


def interpolate(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i-1]) / (xs[i] - xs[i-1])
            return ys[i-1] + t * (ys[i] - ys[i-1])
    raise ValueError('보간 범위를 확인하세요.')


def to_nine(g):
    return interpolate(interpolate(g, FIVE, P5), P9, NINE)


def to_five(g):
    return interpolate(interpolate(g, NINE, P9), P5, FIVE)


def make_plan(required_mean, count, mode):
    """평균을 유지하며 경계에서 자동으로 기울기를 줄인다.
    출력값은 0.01 단위로 내림하여 반올림 탓에 목표를 놓치지 않는다.
    낮은 등급 숫자가 더 우수한 성적이다.
    """
    if count < 1:
        return []
    if count == 1 or mode == 'steady':
        raw = [required_mean] * count
    else:
        # 학기당 기본 0.30등급 변화. 1~5 범위에 맞추어 축소.
        half_width = min(0.30 * (count - 1) / 2,
                         required_mean - 1., 5. - required_mean)
        offsets = [-half_width + 2 * half_width * i / (count - 1)
                   for i in range(count)]
        sign = -1 if mode == 'growth' else 1
        raw = [required_mean + sign * d for d in offsets]
    return [max(1., min(5., math.floor((x + 1e-9) * 100) / 100)) for x in raw]


def main():
    st.set_page_config(page_title='GRADE PATH | 내신 로드맵', page_icon='🎯', layout='wide')
    st.markdown('''<style>
    .stApp {background: #f7f9fc;}
    .block-container {max-width:1100px; padding-top:2rem;}
    h1,h2,h3 {letter-spacing:-0.045em;}
    .grade-pin {position:sticky; top:3.75rem; z-index:990;
      background:#12233f; color:white; padding:18px 24px; border-radius:18px;
      box-shadow:0 8px 24px #14233f20; margin-bottom:22px;
      display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;}
    .grade-pin small {color:#d7e2f6;} .grade-pin strong {font-size:2rem; color:#84ead2;}
    .mode-card {background:white; border:1px solid #e2e8f0; border-radius:16px;
      padding:18px; min-height:145px; margin-bottom:16px;}
    .mode-card p {color:#526277; margin-bottom:0;}
    @media(max-width:640px) {.grade-pin {top:3.5rem; padding:12px 16px;}
      .grade-pin strong {font-size:1.5rem;}}
    </style>''', unsafe_allow_html=True)
    st.caption('GRADE PATH · 나의 내신 목표 설계')
    st.title('지금 성적에서, 목표까지 🎯')
    st.write('5등급제 학기 평균을 입력하면 현재 위치와 남은 학기별 목표를 함께 보여드려요.')

    with st.sidebar:
        st.header('성적 입력')
        completed = st.selectbox('마지막 성적이 나온 학기', list(range(1, 6)),
                                 index=1, format_func=lambda n: SEMESTERS[n-1])
        st.caption('성적이 확정된 학기까지만 입력하세요. 낮은 숫자가 좋은 성적입니다.')
        grades = []
        for i in range(completed):
            grades.append(st.number_input(SEMESTERS[i] + ' 평균', min_value=1., max_value=5.,
                                           value=2.50, step=0.01, format='%.2f',
                                           key=f'grade_{i}', help='5등급제 평균등급 · 1.00~5.00'))
        st.divider()
        target = st.number_input('최종 목표 평균 · 9등급제 추정 기준',
                                 min_value=1., max_value=9., value=3.00,
                                 step=0.01, format='%.2f', key='target')
        st.caption('3학년 1학기까지 총 5개 학기를 동일 비중으로 계산합니다.')

    current = sum(grades) / completed
    current9 = to_nine(current)
    st.markdown(f'''<div class="grade-pin"><div><small>현재 누적 평균 · 9등급제 참고 추정</small><br>
      <strong>{current9:.2f}등급</strong></div><div><small>입력한 5등급제 평균</small><br>
      {current:.2f}등급 · {escape(SEMESTERS[completed-1])}까지</div></div>''', unsafe_allow_html=True)
    st.caption('상단 성적 카드는 화면을 스크롤해도 따라옵니다. 사이드바 입력을 바꾸면 자동으로 다시 계산됩니다.')
    st.warning('참고용 시뮬레이션입니다. 학기 평균만으로 실제 9등급제 성적을 복원할 수 없습니다. '
               '대학별 공식 환산·합격 예측이 아니며 과목별 학점과 학년별 가중치는 반영하지 않습니다.')

    remaining = 5 - completed
    st.subheader('나의 목표 로드맵')
    if remaining == 0:
        if current9 <= target + 1e-9:
            st.success(f'5개 학기 입력 완료! 현재 추정 평균 {current9:.2f}등급으로 목표를 충족합니다.')
        else:
            st.info(f'5개 학기 입력이 완료되어 남은 학기가 없습니다. 목표보다 추정 평균이 {current9-target:.2f}등급 높습니다.')
    else:
        best5 = (sum(grades) + remaining) / 5
        worst5 = (sum(grades) + 5 * remaining) / 5
        best9, worst9 = to_nine(best5), to_nine(worst5)
        a,b,c = st.columns(3)
        a.metric('최종 목표 · 9등급제 추정', f'{target:.2f}등급')
        b.metric('남은 학기', f'{remaining}학기')
        c.metric('모두 1등급일 때 최종 추정', f'{best9:.2f}등급')
        # 목표는 정확히 같은 수치가 아니라 그 수치 이하(더 우수한 성적) 달성이다.
        possible = target >= best9 - 1e-9
        if not possible:
            st.error(f'현재 입력과 추정 방식에서는 목표 달성이 어렵습니다. 남은 학기에 모두 5등급제 1.00등급을 받아도 '
                     f'최종 추정치는 {best9:.2f}등급입니다. 아래는 가능한 최선의 로드맵입니다.')
            required = 1.
        elif target >= worst9 - 1e-9:
            required = 5.
            st.success('현재 성적이면 남은 학기 모두 5.00등급이어도 설정한 목표를 충족합니다. 목표를 더 높여보세요!')
        else:
            target5 = to_five(target)
            required = max(1., min(5., (5 * target5 - sum(grades)) / remaining))
            st.info(f'남은 학기 5등급제 평균이 {required:.3f}등급 이하이면 목표를 충족합니다. '
                    '아래 계획의 학기별 목표를 그대로 따르거나 더 좋은 성적을 받으면 됩니다.')

        modes = [('steady', '⚖️ 꾸준히 모드', '매 학기 비슷하게 · 일정한 페이스로 목표까지'),
                 ('growth', '🚀 우상향 모드', '뒤로 갈수록 더 좋은 등급 · 차근차근 실력 쌓기'),
                 ('front', '🔥 선공후락 모드', '처음에 집중하고, 뒤에는 여유 있게')]
        columns = st.columns(3)
        for col, (key, title, description) in zip(columns, modes):
            with col:
                plan = make_plan(required, remaining, key)
                final5 = (sum(grades) + sum(plan)) / 5
                final9 = to_nine(final5)
                st.markdown(f'<div class="mode-card"><h3>{title}</h3><p>{description}</p></div>', unsafe_allow_html=True)
                st.caption('학기별 목표는 실제 입력 기준인 **5등급제 평균**입니다.')
                rows = [{'남은 학기': SEMESTERS[completed+i], '목표 · 5등급제': f'{g:.2f}등급',
                         '9등급제 참고 추정': f'{to_nine(g):.2f}등급'} for i,g in enumerate(plan)]
                st.dataframe(rows, hide_index=True, use_container_width=True)
                st.metric('최종 누적 · 9등급제 추정', f'{final9:.2f}등급')
                st.caption(f'최종 5등급제 평균 {final5:.3f} · '+
                           ('목표 충족 ✅' if final9 <= target + 1e-8 else '현재 조건의 최선'))
        if remaining == 1:
            st.caption('남은 학기가 한 번이라 세 모드의 계획이 동일합니다.')
        elif required <= 1.000001 or required >= 4.999999:
            st.caption('필요 평균이 1등급 또는 5등급 경계에 있어 세 모드의 계획이 동일합니다.')
        st.caption('모드별 기본 변화 폭은 학기당 0.30등급이며, 1~5등급 경계를 넘지 않도록 자동 축소합니다. '
                   '표시된 목표는 0.01등급 단위로 내림해 소수점 반올림 때문에 목표를 놓치지 않도록 했습니다.')

    with st.expander('계산 방식과 한계 · 꼭 확인하세요'):
        st.markdown('''**계산 기준**
- 입력한 학기 평균을 단순 평균합니다. 모든 학기를 동일하게 반영합니다.
- 5등급제 각 등급의 누적 비율 구간 중앙값 **5, 22, 50, 78, 95%**를 대표 백분위로 가정합니다.
- 소수점 평균등급은 인접 중앙값 사이를 선형 보간합니다.
- 대표 백분위를 9등급제 구간 중앙값 **2, 7.5, 17, 31.5, 50, 68.5, 83, 92.5, 98%**에 선형 보간합니다.
- 최종 성적은 **5개 학기의 5등급제 평균을 먼저 구한 뒤** 위 방식으로 변환합니다. 학기별 9등급 추정치의 평균이 아닙니다.
- 목표는 입력한 9등급제 추정치 **이하**로 해석합니다. 숫자가 낮을수록 좋습니다.

**중요한 한계**
이 보간 공식은 앱이 선택한 계획용 가정이며 공식 환산표가 아닙니다. 평균등급이 같아도 과목별 성적 구성과 석차에 따라 실제 결과는 다릅니다.
5등급제 1.00등급은 이 가정에서 약 1.55등급, 5.00등급은 약 8.45등급입니다.
이는 실제 학생이 9등급제 1등급을 받을 수 없다는 뜻이 아니라, 평균만으로 추정하는 이 방식의 한계입니다.
''')
        st.dataframe([{'입력 · 5등급제': f'{g:.0f}', '참고 추정 · 9등급제': f'{to_nine(g):.2f}'}
                      for g in FIVE], hide_index=True, use_container_width=True)
        st.markdown(f'[등급별 비율 근거: 서울특별시교육청 쎈진학 나침판 · 2028 대입 학생부 변화]({SOURCE})')
        st.caption('위 출처는 등급별 비율의 근거이며, 이 앱의 보간 공식이나 학기별 계획을 공인하는 자료는 아닙니다.')
    st.caption('GRADE PATH · 성적은 가능성을 설계하기 위한 출발점입니다.')


if __name__ == '__main__':
    main()
