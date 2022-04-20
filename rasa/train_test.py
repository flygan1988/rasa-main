from model_training import train
from model_training import train_nlu


if __name__ == '__main__':
    config_path = '../examples/carbot_v2/config.yml'
    training_files = '../examples/carbot_v2/data'
    domain_file = '../examples/carbot_v2/domain.yml'

    train(config=config_path, domain=domain_file, training_files=training_files, fixed_model_name='carbot_v2_0402', output='models')
    #train_nlu(config=config_path, nlu_data=training_files, fixed_model_name="chinesebot_nlu", output="models", domain=domain_file)