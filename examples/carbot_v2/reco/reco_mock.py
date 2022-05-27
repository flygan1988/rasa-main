# -*- coding:utf-8 -*-
# 推荐模块入口
import random


def reco_car_model(car_int: list, reco_his: dict = None) -> tuple:
    """
    这是车型推荐的主函数,用于与对话系统对接

    入参举例：
        car_int = [{
                'car_series':['朗逸'],
                'version':['风尚版'],
                'year':[2022],
                'liter': ['1.4T'],
                'gear_type':['手动'],
                'body_type':['SUV'],
                'model_price':[10000,100000],
                'model_space':['紧凑型'],
                'fuel_type':['纯电'],
                'seat_number':[7],
                'favor':['性价比高','最好看的']
            }],
        reco_his = {'朗逸2022款1.5L自动风尚版':1}
    出参举例：
        ([['朗逸2022款1.5L自动风尚版',],],[0,])
    具体参考手册
    """
    rmd_rst = []
    rst_dsc = []

    for i, x in enumerate(car_int):
        print('第%d组' % (i + 1))
        print('输入项 car_series: ', x.get('car_series'))
        print('输入项 version: ', x.get('version'))
        print('输入项 year: ', x.get('year'))
        print('输入项 liter: ', x.get('liter'))
        print('输入项 gear_type: ', x.get('gear_type'))
        print('输入项 body_type: ', x.get('body_type'))
        print('输入项 model_price: ', x.get('model_price'))
        print('输入项 model_space: ', x.get('model_space'))
        print('输入项 fuel_type: ', x.get('fuel_type'))
        print('输入项 seat_number: ', x.get('seat_number'))
        print('输入项 favor: ', x.get('favor'))
        temp_a = random.randint(0, 4)
        if temp_a < 4:
            rmd_rst.append(['2022款 朗逸 1.5L 自动风尚版', '2022款 朗逸 1.5L 自动舒适版'])
            rst_dsc.append(temp_a)
        else:
            rmd_rst.append([])
            rst_dsc.append(temp_a)
    return rmd_rst, rst_dsc


if __name__ == '__main__':
    rmd_rst, rst_dsc = reco_car_model([{
        'car_series': ['朗逸'],
        'version': ['风尚版'],
        'year': [2022],
        'liter': ['1.4T'],
        'gear_type': ['手动'],
        'body_type': ['SUV'],
        'model_price': [10000, 100000],
        'model_space': ['紧凑型'],
        'fuel_type': ['新能源'],
        'seat_number': [7],
        'favor': ['性价比高', '最好看的']
    }, {
        'car_series': ['朗逸'],
        'version': ['风尚版'],
        'year': [2022],
        'liter': ['1.4T'],
        'gear_type': ['手动'],
        'body_type': ['SUV'],
        'model_price': [10000, 100000],
        'model_space': ['紧凑型'],
        'fuel_type': ['纯电'],
        'seat_number': [7],
        'favor': ['性价比高', '最好看的']
    }])
    print(rmd_rst, rst_dsc)
