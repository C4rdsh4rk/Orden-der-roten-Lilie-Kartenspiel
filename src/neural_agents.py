"""Module for agents that use NNs"""


import tensorflow as tf
from tensorflow import keras


class CrashMasterFlex(keras.Model):
    """
    :param observation_space: (gym.Space)
    :param features_dim: (int) Number of features extracted.
        This corresponds to the number of unit for the last layer.
    """

    def __init__(self, observation_space: gym.spaces.Box, num_numeric_features: int = 256, hand_max_cards=20):
        """Initializer, CAREFULL, hand_max_cards should be smaller than card_embedding_dim, otherwise the
        NN will not work.

        Args:
            observation_space (gym.spaces.Box): _description_
            num_numeric_features (int, optional): _description_. Defaults to 256.
            hand_max_cards (int, optional): _description_. Defaults to 20.
        """
        super().__init__()
        self.hand_max_cards = hand_max_cards + 1 # add id=0 for passing
        self.num_card_features = 3
        self.card_embedding_dim = 32
        self.numeric_state_emb_dim = 32
        self.card_embedder = self.get_card_embedder()
        self.state_embedder = self.get_numeric_state_embedder(num_numeric_features)
        self.action_extractor = self.get_action_extractor(num_cards=self.hand_max_cards)
        # FRONT = 1
        # WISE = 2
        # SUPPORT = 3
        # EFFECTS = 4
        # ANY = 5
        self.masking_profiles = tf.Tensor([
            [1, 0, 0, 0, 0, 0, 0], # not playable in any board row
            [0, 1, 0, 0, 0, 0, 0], # only playable in player from row
            [0, 0, 1, 0, 0, 0, 0], # only playable in player mid row
            [0, 0, 0, 1, 0, 0, 0], # only playable in player support row
            [0, 1, 1, 1, 0, 0, 0], # only playable for player
            [0, 0, 0, 0, 1, 1, 1] # only playable to enemy
        ])

    def get_card_embedder(self):
        """Creates the (shared model) that is responsible for embedding cards"""
        embedding_input = keras.Input(shape=(self.card_features,))
        embedding = keras.layers.Dense(self.card_embedding_dim*2)(embedding_input)
        embedding = keras.layers.Dense(self.card_embedding_dim)(embedding)
        return keras.Model(embedding_input, embedding)

    def get_numeric_state_embedder(self, num_vars):
        """Creates a small model that embeds the numeric input values"""
        embedding_input = keras.Input(shape=(num_vars,))
        embedding = keras.layers.Dense(self.numeric_state_emb_dim)(embedding_input)
        return keras.Model(embedding_input, embedding)
    
    def embed_cards(self, cards: tf.Tensor) -> tf.Tensor:
        """Takes a tensor of cards (the last dim is the one indicating the card index),
        and transforms it to an embedding of one less dimension (a single embedding for all cards).

        Args:
            cards (tf.Tensor): 

        Returns:
            tf.Tensor: 
        """
        num_cards = cards.shape[-1]
        card_embeddings = tf.zeros(shape=(self.card_embedding_dim, num_cards))
        for card_index in range(num_cards):
            card_embeddings[:, card_index] = self.card_embedder(cards[:, card_index])
        return tf.reduce_mean(card_embeddings, axis=-1, keep_dims=False, name='card_embedding_pooling')
    
    def get_action_extractor(self, num_cards, num_rows=7):
        """NN that transforms its input (general state embedding into actions). Note
        that card_id==0 is passing and row_id==0 means no row was selected (for cards that
        are not playable in a row)

        Returns:
            keras.Model: main model that transforms the state embedding to an action
        """
        state_embedding = keras.layers.Input(shape=(self.card_embedding_dim, 7))
        masking_vector_cards_input = keras.layers.Input(shape=(self.card_embedding_dim, 1))
        masking_vector_cards = masking_vector_cards_input[0:self.hand_max_cards, 0]

        masking_vector_rows_input = keras.layers.Input(shape=(self.card_embedding_dim, 1))
        masking_vector_rows = masking_vector_rows_input[0:self.hand_max_cards, 0]

        hidden = keras.layers.Dense(256, activation='relu')(state_embedding)
        hidden = keras.layers.Dense(128, activation='relu')(hidden)
        hidden = keras.layers.Dense(64, activation='relu')(hidden)
        hidden = keras.layers.LSTM(32, activation='relu')(hidden)

        # apply masking (if less than num_cards are in hand)
        card_id = keras.layers.Dense(num_cards, activation='relu')(hidden)
        card_mask = tf.math.multiply(masking_vector_cards, -1e9)
        tf.debugging.assert_rank(card_id, card_mask)
        card_id = tf.math.add(card_id, card_mask, name="card_id_masking")
        card_id = keras.layers.Softmax()(card_id)
        # apply masking (for normal cards, only the own rows should be valid)
        row_id = keras.layers.Dense(num_rows, activation='relu')(hidden)
        # find the masking from the card that is currently selected
        row_profile = masking_vector_rows[tf.argmax(card_id)]
        # get the profile and multiply with large number
        row_mask = tf.math.multiply(self.masking_profiles[row_profile], -1e9)
        tf.debugging.assert_rank(row_id, row_mask)
        row_id = tf.math.add(row_id, row_mask, name="row_id_masking")
        row_id = keras.layers.Softmax()(row_id)

        return keras.Model([state_embedding, masking_vector_cards_input, masking_vector_rows_input], [card_id, row_id])
    
    def train_step(self, player_hand: tf.Tensor, p_row0, p_row1, p_row2, op_row0, op_row1, op_row2, numerics):
        """Train step function of the model

        Args:
            player_hand (tf.Tensor): matrix of card representations that are currently on the players hand
            p_row0 (_type_): matrix of card representations of the front row of the observable player
            p_row1 (_type_): matrix of card representations of the mid row of the observable player
            p_row2 (_type_): matrix of card representations of the support row of the observable player
            op_row0 (_type_): matrix of card representations of the front row of the opponent
            op_row1 (_type_): matrix of card representations of the mid row of the opponent
            op_row2 (_type_): matrix of card representations of the support row of the opponent
            numerics (_type_): vector representation of the current values of the board (num_stack_cards, num_deck_card
            num_graveyard_cards, num_graveyard_cards_op, rows_won, op_rows_won, rounds_won, rounds_won_op, rounds_left
            row_scores (6x))
        """
        num_cards = player_hand.shape[-1] + 1  # (we can always play pass)

        card_id_mask = tf.concat([  # only the first max_card_hand are used anyway
            tf.zeros(shape=(num_cards)),  # zeros are not masked values
            tf.ones(shape=(self.card_embedding_dim-num_cards)),  # these values are masked 
        ])
        row_id_mask = tf.concat([  # only the first max_card_hand
            player_hand[:, 1],
            tf.zeros(shape=(self.card_embedding_dim-num_cards,))
        ])
        row_id_mask[tf.where(row_id_mask == 4)] = 0  # 4 is effect card (not playable on board)
        row_id_mask[tf.where(row_id_mask == 5)] = 4  # 5 is any row, which means only our rows
        # embed cards and numeric state into a single matrix
        card_embeddings = tf.concat([
            self.embed_cards(player_hand),
            self.embed_cards(p_row0),
            self.embed_cards(p_row1),
            self.embed_cards(p_row2),
            self.embed_cards(op_row0),
            self.embed_cards(op_row1),
            self.embed_cards(op_row2)
        ])
        state_embedding = self.state_embedder(numerics)

        embeddings = tf.concat([card_embeddings, state_embedding, card_id_mask, row_id_mask])
        # use the main model to get back the card_id and row that should be used (masks are provided)
        card_id, row = self.action_extractor(embeddings)
        return
        
        